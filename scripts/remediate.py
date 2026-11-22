"""Propose dependency security bumps; recipes apply the committed list with omnibump.

The planner runs inside Melange, after the recipe's own source preparation, and writes
`plan.json`. `write` turns that plan into the `deps` input of the recipe's
`eudaldgr-labs/bump` step, so every build is a function of the committed recipe.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request


PIPELINE = 'eudaldgr-labs/bump'
PLANNER = 'eudaldgr-labs/remediate-plan'
ECOSYSTEMS = {'go': 'Go', 'rust': 'crates.io', 'js': 'npm'}
MANIFESTS = {'go': ['go.mod', 'go.sum', 'go.work', 'go.work.sum'],
             'rust': ['Cargo.toml', 'Cargo.lock'],
             'js': ['package.json', 'pnpm-lock.yaml', 'pnpm-workspace.yaml']}
LOCKFILES = {'go': 'go.mod', 'rust': 'Cargo.lock', 'js': 'pnpm-lock.yaml'}
OUT = Path('out/remediation')


class PolicyError(ValueError):
    pass


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def run(*args, cwd=None, codes=(0,)):
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env={**os.environ, 'GOTOOLCHAIN': 'local', 'npm_config_ignore_scripts': 'true'},
                            timeout=1200)
    if result.returncode not in codes:
        raise subprocess.CalledProcessError(result.returncode, args, output=result.stdout, stderr=result.stderr)
    if result.stderr:
        print(result.stderr, file=sys.stderr, end='')
    return result.stdout


# Planning: these functions run inside the Melange planner.

def version(value):
    # Stable SemVer only; prereleases and Go pseudo-versions are never proposed.
    match = re.fullmatch(r'v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:\+incompatible)?', value)
    return tuple(map(int, match.groups())) if match else None


# Modules that stay on 0.x by convention while keeping compatibility across minors.
ZERO_MINOR_COMPATIBLE = ('golang.org/x/',)


def allowed(old, new, level, name=''):
    a, b = version(old), version(new)
    zero_minor = name.startswith(ZERO_MINOR_COMPATIBLE)
    return bool(a and b and b > a and (a[:2] == b[:2] if level == 'patch'
                                      else a[0] == b[0] and (a[0] != 0 or a[1] == b[1] or zero_minor)))


def records(report):
    if not isinstance(report, dict) or not isinstance(report.get('results'), list):
        raise ValueError('Invalid OSV report')
    result = {}
    for source in report['results']:
        for entry in source['packages']:
            package = entry['package']
            key = tuple(package.get(k, '') for k in ('ecosystem', 'name', 'version'))
            if not all(key):
                raise ValueError(f'Unversioned or unidentified dependency: {package}')
            vulnerabilities = result.setdefault(key, {})
            for vuln in entry.get('vulnerabilities', []):
                if not vuln.get('withdrawn'):
                    vulnerabilities[vuln['id']] = vuln
    if not result:
        raise ValueError('OSV returned no dependency inventory')
    return result


def query(package, target):
    data = encoded({'package': {'ecosystem': package[0], 'name': package[1]}, 'version': target})
    for attempt in range(3):
        try:
            request = urllib.request.Request('https://api.osv.dev/v1/query', data=data,
                                             headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.load(response)
            if (not isinstance(result, dict) or set(result) - {'vulns', 'next_page_token'}
                    or not isinstance(result.get('vulns', []), list)
                    or result.get('next_page_token') and not result.get('vulns')):
                raise ValueError('Invalid OSV query response')
            return result
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def select_updates(inventory, level, language):
    """Pick, per vulnerable version, the lowest allowed release with no known advisory."""
    updates, blocked = [], []
    for package, vulns in sorted(inventory.items()):
        if not vulns:
            continue
        candidates = set()
        for vuln in vulns.values():
            for affected in vuln.get('affected', []):
                if affected.get('package', {}).get('name') != package[1] or affected['package'].get('ecosystem') != package[0]:
                    continue
                for affected_range in affected.get('ranges', []):
                    if affected_range['type'] in {'SEMVER', 'ECOSYSTEM'}:
                        candidates.update(e['fixed'] for e in affected_range['events'] if 'fixed' in e)
        candidates = sorted((v for v in candidates if allowed(package[2], v, level, package[1])), key=version)
        target = None
        if package[0] == ECOSYSTEMS[language]:
            for candidate in candidates:
                if not any(not v.get('withdrawn') for v in query(package, candidate).get('vulns', [])):
                    target = candidate
                    break
        item = dict(ecosystem=package[0], name=package[1], old=package[2], vulnerabilities=sorted(vulns),
                    aliases=sorted({alias for v in vulns.values() for alias in [v['id'], *v.get('aliases', [])]}))
        if target:
            updates.append(dict(item, new=target))
        else:
            blocked.append(dict(item, reason=f'No known vulnerability-free {level} fix'))
    return updates, blocked


def validate_graph(before, after, updates, level):
    for ecosystem, name, old in before:
        remaining = [v for e, n, v in after if (e, n) == (ecosystem, name)]
        if remaining and old not in remaining and not any(
                version(old) and version(v) and version(v) >= version(old) for v in remaining):
            raise PolicyError(f'Resolver downgraded dependency: {name}@{old}')
    for ecosystem, name, current in after:
        previous = [v for e, n, v in before if (e, n) == (ecosystem, name)]
        if previous and current not in previous and not any(allowed(v, current, level, name) for v in previous):
            raise PolicyError(f'Resolver changed dependency outside policy: {name}: {previous} -> {current}')
    old_findings = {(e, n, v, ident) for (e, n, v), vulns in before.items() for ident in vulns}
    new_findings = {(e, n, v, ident) for (e, n, v), vulns in after.items() for ident in vulns} - old_findings
    if new_findings:
        raise PolicyError(f'Resolution introduced vulnerable dependencies: {sorted(new_findings)}')
    for update in updates:
        resolved = [(key, vulns) for key, vulns in after.items()
                    if key[:2] == (update['ecosystem'], update['name'])]
        if not any(version(key[2]) == version(update['new']) and not vulns for key, vulns in resolved):
            raise PolicyError(f'Requested fix did not land: {update["name"]}@{update["new"]}')
        if (update['ecosystem'], update['name'], update['old']) in after:
            raise PolicyError(f'Vulnerable version remains installed: {update["name"]}@{update["old"]}')


def pin(update, language):
    """The `deps` line for an update, in the format bump.yaml splits on its last `@`."""
    if language == 'go':
        return f'{update["name"]}@v{update["new"].removeprefix("v")}'
    if language == 'js':
        # A version selector keeps other installed versions of the same package untouched.
        return f'{update["name"]}@{update["old"]}@{update["new"]}'
    return f'{update["name"]}@{update["new"]}'


def parse_pins(text):
    result = []
    for line in (text or '').splitlines():
        line = line.strip()
        if not line:
            continue
        name, separator, value = line.rpartition('@')
        if not separator or not name or not value:
            raise ValueError(f'Invalid dependency pin: {line}')
        result.append({'name': name, 'version': value})
    return result


def apply_pins(language, pins, workdir):
    """Apply pins exactly as the build's bump.yaml does: one omnibump call."""
    if not pins:
        return
    deps = Path(workdir) / 'deps.json'
    write_json(deps, {'packages': parse_pins('\n'.join(pins))})
    if language == 'go':
        run('omnibump', '--language', 'go', '--deps', str(deps), '--tidy')
    elif language == 'rust':
        run('omnibump', '--language', 'rust', '--deps', str(deps), '--fail-on-unapplied-pins')
    else:
        run('omnibump', '--language', 'js', '--manager', 'pnpm', '--deps', str(deps))
        run('pnpm', 'install', '--lockfile-only', '--ignore-scripts', '--no-frozen-lockfile')


def roots(language):
    result = [Path('.')]
    if language == 'go' and Path('go.work').exists():
        workspace = json.loads(run('go', 'work', 'edit', '-json'))
        result = [Path(p['DiskPath']) for p in workspace['Use']]
    for root in result:
        root.resolve().relative_to(Path.cwd().resolve())
        if root.is_symlink():
            raise ValueError('Symlink project root')
    return sorted(set(result))


def manifests(language, project_roots):
    paths = {str(root / name) for root in project_roots for name in MANIFESTS[language]}
    if language == 'go':
        paths.update(['go.work', 'go.work.sum'])
    if language == 'rust':
        paths.update(str(p) for p in Path('.').rglob('Cargo.toml') if '.git' not in p.parts)
    return sorted(paths)


def snapshot(paths):
    result = {}
    for name in paths:
        path = Path(name)
        path.resolve().relative_to(Path.cwd().resolve())
        if path.is_symlink():
            raise ValueError(f'Symlink manifest: {name}')
        result[name] = path.read_bytes() if path.exists() else None
    return result


def restore(files):
    for name, content in files.items():
        if content is None:
            Path(name).unlink(missing_ok=True)
        else:
            Path(name).write_bytes(content)


def scan(language, project_roots, output, workdir):
    args = ['osv-scanner', 'scan', 'source', '--all-packages', '--all-vulns', '--no-call-analysis=go,rust',
            '--no-ignore', '--format=json', '--output-file', str(output)]
    # An empty config prevents upstream ignore lists from hiding dependencies.
    config = Path(workdir) / 'empty.toml'
    config.write_text('')
    args.extend(['--config', str(config)])
    for root in project_roots:
        args.extend(['--lockfile', str(root / LOCKFILES[language])])
    run(*args, codes=(0, 1))
    report = json.loads(Path(output).read_text())
    records(report)
    return report


def tail(error, size=600):
    text = ((error.stderr or '') + (error.output or '')).strip()
    return text[-size:] or str(error)


def first_line(text):
    return text.strip().splitlines()[0] if text.strip() else ''


def tool_version(text):
    # omnibump prints a banner before its build metadata.
    match = re.search(r'^GitVersion:\s*(\S+)', text, re.M)
    return match[1] if match else first_line(text)


def create_plan(language, level, modroot):
    out = Path('.remediation').resolve()
    out.mkdir(exist_ok=True)
    try:
        commit = run('git', 'rev-parse', 'HEAD').strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    os.chdir(modroot)
    project_roots = roots(language)
    original = snapshot(manifests(language, project_roots))
    before = records(scan(language, project_roots, out / 'scan-before.json', out))
    updates, blocked = select_updates(before, level, language)
    accepted = []
    # Each proposal is tried together with the already accepted ones, from the pristine
    # manifests, exactly as the build will apply the final list.
    for update in updates:
        restore(original)
        try:
            apply_pins(language, [pin(u, language) for u in [*accepted, update]], out)
        except subprocess.CalledProcessError as error:
            reason = 'omnibump could not apply this pin: ' + tail(error)
        else:
            try:
                validate_graph(before, records(scan(language, project_roots, out / 'scan-candidate.json', out)),
                               [*accepted, update], level)
            except PolicyError as error:
                reason = str(error)
            else:
                accepted.append(update)
                continue
        blocked.append(dict(update, reason=reason))
        print(f'Remediation pending: {update["name"]}: {reason}', file=sys.stderr)
    restore(original)
    pins = sorted(pin(u, language) for u in accepted)
    apply_pins(language, pins, out)
    after = records(scan(language, project_roots, out / 'scan-after.json', out))
    validate_graph(before, after, accepted, level)
    restore(original)
    plan = dict(schema=2, language=language, policy=level, modroot=modroot, source=commit, deps=pins,
                updates=accepted, blocked=sorted(blocked, key=lambda b: (b['name'], b['old'])),
                reports={name: digest((out / name).read_bytes()) for name in ['scan-before.json', 'scan-after.json']},
                tools={'osv-scanner': first_line(run('osv-scanner', '--version')),
                       'omnibump': tool_version(run('omnibump', 'version'))})
    write_json(out / 'plan.json', plan)
    print(f'Remediation: {len(pins)} pins, {len(plan["blocked"])} pending ({level} policy)')


# Host side: preparing the planner, reading its result and editing the recipe.

def load_plan(path):
    plan = json.loads(Path(path).read_text())
    if (plan.get('schema') != 2 or plan.get('language') not in ECOSYSTEMS
            or plan.get('policy') not in {'patch', 'minor'} or not isinstance(plan.get('deps'), list)):
        raise ValueError('Invalid remediation plan')
    parse_pins('\n'.join(plan['deps']))
    return plan


def check_name(name):
    if not name or Path(name).name != name or name in {'.', '..', 'out'}:
        raise ValueError('Expected a top-level package directory')


def recipe(name):
    import yaml
    check_name(name)
    config = yaml.safe_load((Path(name) / 'melange.yaml').read_text())
    steps = [(i, p) for i, p in enumerate(config['pipeline']) if p.get('uses') == PIPELINE]
    if len(steps) > 1:
        raise ValueError('Use one bump step per recipe')
    if steps and steps[0][1].get('with', {}).get('language') not in ECOSYSTEMS:
        raise ValueError(f'{name}: bump step needs language: {", ".join(ECOSYSTEMS)}')
    return config, steps[0] if steps else None


def opted(root=Path('.'), base=None):
    names = sorted(p.parent.name for p in root.glob('*/melange.yaml') if recipe(p.parent.name)[1])
    if base:
        changed = {Path(f).parts[0] for f in run('git', 'diff', '--name-only', f'{base}...HEAD').splitlines() if f}
        names = [n for n in names if n in changed]
    return names


def prepare_plan(name, arch):
    import yaml
    if arch not in {'x86_64', 'aarch64'}:
        raise ValueError(f'Unsupported architecture: {arch}')
    config, step = recipe(name)
    if not step:
        raise ValueError(f'{name} has no {PIPELINE} step')
    destination = OUT / name
    context = destination / 'planner-context'
    shutil.rmtree(context, ignore_errors=True)
    (destination / 'plan.json').unlink(missing_ok=True)
    shutil.copytree(name, context)
    helper = context / '.remediation'
    helper.mkdir()
    shutil.copy2(__file__, helper / 'engine.py')
    for key in ['test', 'subpackages', 'update']:
        config.pop(key, None)
    config['package'].pop('dependencies', None)
    index, bump = step
    inputs = {k: v for k, v in bump.get('with', {}).items() if k in {'language', 'modroot', 'policy'}}
    go_packages = sorted({p.get('with', {}).get('go-package', 'go') for p in config['pipeline'] if p.get('uses') == 'go/build'})
    config['pipeline'] = config['pipeline'][:index] + [
        {'uses': PLANNER, 'with': inputs},
        {'runs': 'mkdir -p "${{targets.destdir}}/usr/share/remediation"\n'
                 'cp .remediation/plan.json .remediation/scan-*.json "${{targets.destdir}}/usr/share/remediation/"'}]
    packages = config.setdefault('environment', {}).setdefault('contents', {}).setdefault('packages', [])
    if inputs['language'] == 'go':
        packages.extend(go_packages or ['go'])
    elif inputs['language'] == 'rust':
        packages.append('rust')
    config['environment'].get('environment', {}).pop('GOFLAGS', None)
    (context / 'plan.yaml').write_text(yaml.safe_dump(config, sort_keys=False))
    return str(context)


def extract_plan(name, arch):
    destination = OUT / name
    package = recipe(name)[0]['package']
    filename = f'{package["name"]}-{package["version"]}-r{package.get("epoch", 0)}.apk'
    with tarfile.open(destination / 'packages' / arch / filename, 'r:gz', ignore_zeros=True) as archive:
        for item in ['plan.json', 'scan-before.json', 'scan-after.json']:
            (destination / item).write_bytes(archive.extractfile('usr/share/remediation/' + item).read())
    load_plan(destination / 'plan.json')


def set_deps(text, pins):
    """Rewrite the `deps` input of the bump step, preserving the rest of the file byte for byte."""
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if re.fullmatch(r'\s*- uses: ' + re.escape(PIPELINE) + r'\s*', line)), None)
    if start is None:
        raise ValueError(f'No {PIPELINE} step')
    indent = len(lines[start]) - len(lines[start].lstrip())

    def depth(line):
        return len(line) - len(line.lstrip()) if line.strip() else None

    end = next((i for i in range(start + 1, len(lines)) if depth(lines[i]) is not None and depth(lines[i]) <= indent), len(lines))
    key = next((i for i in range(start + 1, end) if re.match(r'\s*deps:', lines[i])), None)
    if key is None:
        raise ValueError(f'The {PIPELINE} step needs a `deps:` input, for example deps: ""')
    key_indent = depth(lines[key])
    stop = next((i for i in range(key + 1, end) if depth(lines[i]) is not None and depth(lines[i]) <= key_indent), end)
    while stop > key + 1 and not lines[stop - 1].strip():
        stop -= 1
    prefix = ' ' * key_indent
    block = [f'{prefix}deps: ""\n'] if not pins else [f'{prefix}deps: |-\n', *[f'{prefix}  {p}\n' for p in pins]]
    return ''.join(lines[:key] + block + lines[stop:])


def bump_epoch(text):
    updated, count = re.subn(r'(?m)^(\s+epoch:[ \t]*)(\d+)', lambda m: f'{m[1]}{int(m[2]) + 1}', text, count=1)
    if not count:
        raise ValueError('Recipe has no epoch')
    return updated


def released(name, base):
    """Whether the current package version and epoch already exist on the base branch."""
    import yaml
    try:
        previous = yaml.safe_load(run('git', 'show', f'{base}:{name}/melange.yaml'))['package']
    except (subprocess.CalledProcessError, TypeError, KeyError):
        return False
    current = recipe(name)[0]['package']
    return (str(previous['version']), previous.get('epoch', 0)) == (str(current['version']), current.get('epoch', 0))


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def summary(name, plan):
    package = recipe(name)[0]['package']
    lines = [f'## Dependency security bumps for `{name}`', '',
             f'`{package["name"]}` {package["version"]} — {plan["language"]}, `{plan["policy"]}` policy'
             + (f', upstream commit `{plan["source"][:12]}`' if plan.get('source') else '') + '.', '']
    if plan['updates']:
        lines += ['| Dependency | From | To | Advisories |', '| --- | --- | --- | --- |']
        lines += [f'| `{cell(u["name"])}` | {cell(u["old"])} | {cell(u["new"])} | {cell(", ".join(u["vulnerabilities"]))} |'
                  for u in plan['updates']]
    else:
        lines.append('No compatible fix is available; the committed pins are cleared.')
    if plan['blocked']:
        lines += ['', '### Pending', '', '| Dependency | Version | Advisories | Reason |', '| --- | --- | --- | --- |']
        lines += [f'| `{cell(b["name"])}` | {cell(b["old"])} | {cell(", ".join(b["vulnerabilities"]))} | {cell(b["reason"][:300])} |'
                  for b in plan['blocked']]
    lines += ['', f'Generated by `just remediate {name}`. The build applies `deps` with omnibump; '
              'pending findings stay advisory until upstream or the policy changes.', '']
    return '\n'.join(lines)


def write(name, base):
    plan = load_plan(OUT / name / 'plan.json')
    path = Path(name) / 'melange.yaml'
    text = path.read_text()
    updated = set_deps(text, plan['deps'])
    changed = updated != text
    if changed and released(name, base):
        updated = bump_epoch(updated)
    if changed:
        _, step = recipe_from_text(updated)
        if (step[1]['with'].get('deps') or '') != '\n'.join(plan['deps']):
            raise ValueError('Rewritten recipe does not contain the planned pins')
        path.write_text(updated)
    (OUT / name / 'pr.md').write_text(summary(name, plan))
    print(f'{name}: {"updated" if changed else "unchanged"} ({len(plan["deps"])} pins)')


def recipe_from_text(text):
    import yaml
    config = yaml.safe_load(text)
    steps = [(i, p) for i, p in enumerate(config['pipeline']) if p.get('uses') == PIPELINE]
    return config, steps[0] if steps else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['plan', 'prepare-plan', 'extract', 'write', 'opted'])
    parser.add_argument('name', nargs='?')
    parser.add_argument('arch', nargs='?', default='aarch64')
    parser.add_argument('--language', choices=ECOSYSTEMS)
    parser.add_argument('--policy', choices=['patch', 'minor'], default='patch')
    parser.add_argument('--modroot', default='.')
    parser.add_argument('--base', default=os.environ.get('REMEDIATION_BASE', 'origin/main'))
    parser.add_argument('--changed', action='store_true', help='opted: only recipes changed since --base')
    args = parser.parse_args()
    if args.command == 'plan':
        create_plan(args.language, args.policy, args.modroot)
    elif args.command == 'prepare-plan':
        print(prepare_plan(args.name, args.arch))
    elif args.command == 'extract':
        extract_plan(args.name, args.arch)
    elif args.command == 'write':
        write(args.name, args.base)
    else:
        names = opted(base=args.base if args.changed else None)
        print(json.dumps(names))
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
                output.write(f'packages={json.dumps(names)}\n')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr, file=sys.stderr)
        raise SystemExit(f'Remediation failed: {error}') from error
