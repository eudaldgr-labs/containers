"""Discover local APK dependencies and reject missing build artifacts."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import yaml

APPS = 'apps'


def read(path):
    return yaml.safe_load(path.read_text())


def catalog(root):
    recipes = {p.parent.name: read(p) for p in sorted((root / APPS).glob('*/melange.yaml'))}
    providers = {}
    for directory, recipe in recipes.items():
        package = recipe['package']
        names = [package['name']] + [p['name'] for p in recipe.get('subpackages', [])]
        for name in names:
            name = name.replace('${{package.name}}', package['name'])
            if name in providers:
                raise ValueError(f'Duplicate local package: {name}')
            providers[name] = (directory, f"{name}-{package['version']}-r{package.get('epoch', 0)}.apk")
    return recipes, providers


def requirements(recipe, kind):
    if kind == 'apko':
        return recipe['contents']['packages']
    if kind == 'test':
        return recipe.get('test', {}).get('environment', {}).get('contents', {}).get('packages', []) + [recipe['package']['name']]
    return (recipe.get('package', {}).get('dependencies', {}).get('runtime', [])
            + recipe.get('environment', {}).get('contents', {}).get('packages', [])
            + recipe.get('test', {}).get('environment', {}).get('contents', {}).get('packages', []))


def local_requirements(recipe, kind, providers):
    return {re.split(r'[<>=~]', p, maxsplit=1)[0] for p in requirements(recipe, kind)
            if re.split(r'[<>=~]', p, maxsplit=1)[0] in providers}


def graph(root):
    recipes, providers = catalog(root)
    return {name: {providers[p][0] for p in local_requirements(recipe, 'melange', providers)} - {name}
            for name, recipe in recipes.items()}


def order(root, name, kind):
    recipes, providers = catalog(root)
    deps = graph(root)
    if name == 'all':
        wanted = set(recipes)
    else:
        path = root / APPS / name / f'{kind}.yaml'
        if not path.is_file():
            raise ValueError(f'Unknown {kind} recipe: {name}')
        wanted = {providers[p][0] for p in local_requirements(read(path), kind, providers)}
        if kind == 'melange':
            wanted.add(name)
    result = []
    visiting = set()

    def visit(package):
        if package in visiting:
            raise ValueError(f'Circular dependency: {package}')
        if package in result:
            return
        visiting.add(package)
        for dependency in sorted(deps[package]):
            visit(dependency)
        visiting.remove(package)
        result.append(package)

    for package in sorted(wanted):
        visit(package)
    return result


def affected(root, changes):
    recipes, providers = catalog(root)
    images = {p.parent.name for p in (root / APPS).glob('*/apko.yaml')}
    changed = set()
    for filename in changes:
        path = Path(filename)
        if path.suffix == '.md' or path.parts[0] in {'.assets', '.report', 'reports'}:
            continue
        if len(path.parts) < 3 or path.parts[0] != APPS or path.parts[1] not in recipes.keys() | images:
            return set(recipes), images
        changed.add(path.parts[1])
    deps = graph(root)
    while True:
        expanded = changed | {n for n, ds in deps.items() if ds & changed}
        if expanded == changed:
            break
        changed = expanded
    selected = {name for name in images if name in changed or
                {providers[p][0] for p in local_requirements(read(root / APPS / name / 'apko.yaml'), 'apko', providers)} & changed}
    needed = changed & recipes.keys()
    for name in selected:
        needed.update(order(root, name, 'apko'))
    for name in list(needed):
        needed.update(order(root, name, 'melange'))
    return needed, selected


def discover(root, max_tier=2, changes=None):
    deps = graph(root)
    wanted, images = affected(root, changes) if changes is not None else (
        set(deps), {p.parent.name for p in (root / APPS).glob('*/apko.yaml')})
    levels = {}
    while len(levels) < len(deps):
        ready = {name: max((levels[d] + 1 for d in dependencies), default=0)
                 for name, dependencies in deps.items()
                 if name not in levels and dependencies <= levels.keys()}
        if not ready:
            raise ValueError(f'Circular dependency: {sorted(deps.keys() - levels.keys())}')
        if max(ready.values()) > max_tier:
            raise ValueError(f'Dependency depth exceeds {max_tier}')
        levels.update(ready)
    outputs = {'base_packages': sorted(n for n, level in levels.items() if level == 0 and n in wanted)}
    outputs.update({f'deps_tier_{i}': sorted(n for n, level in levels.items() if level == i and n in wanted)
                    for i in range(1, max_tier + 1)})
    outputs['apko_images'] = sorted(images)
    return outputs


def check(root, name, kind, arch):
    _, providers = catalog(root)
    recipe = read(root / APPS / name / f'{kind}.yaml')
    missing = []
    for package in sorted(local_requirements(recipe, kind, providers)):
        directory, filename = providers[package]
        if kind == 'melange' and directory == name:
            continue
        if not (root / os.environ.get('PACKAGES_DIR', 'packages') / arch / filename).is_file():
            missing.append(f'{directory}/{arch}: {filename}')
    if missing:
        raise ValueError('Required local builds unavailable: ' + ', '.join(missing))


def download(root, name, kind, arch):
    for package in order(root, name, kind):
        if kind == 'melange' and package == name:
            continue
        subprocess.run(['gh', 'run', 'download', os.environ['GITHUB_RUN_ID'],
                        '--repo', os.environ['GITHUB_REPOSITORY'], '--name', f'packages-{package}-{arch}'],
                       cwd=root, check=True)
    check(root, name, kind, arch)


def stage(root, name, arch):
    _, providers = catalog(root)
    destination = root / 'out' / 'artifacts' / 'packages' / arch
    destination.mkdir(parents=True, exist_ok=True)
    for owner, filename in providers.values():
        if owner == name:
            shutil.copy2(root / os.environ.get('PACKAGES_DIR', 'packages') / arch / filename, destination / filename)


def pins(root, name, kind):
    recipes, providers = catalog(root)
    recipe = read(root / APPS / name / ('melange.yaml' if kind == 'test' else f'{kind}.yaml'))
    result = []
    for package in sorted(local_requirements(recipe, kind, providers)):
        directory, _ = providers[package]
        if kind == 'melange' and directory == name:
            continue
        metadata = recipes[directory]['package']
        flag = '--test-package-append' if kind == 'test' else '--package-append'
        result.extend([flag, f"{package}={metadata['version']}-r{metadata.get('epoch', 0)}"])
    return result


if __name__ == '__main__':
    root = Path.cwd()
    try:
        if sys.argv[1] == 'discover':
            changes = None
            if os.environ.get('BASE_SHA'):
                changes = subprocess.check_output(['git', 'diff', '--name-only', os.environ['BASE_SHA'], 'HEAD'], text=True).splitlines()
            outputs = discover(root, int(os.environ.get('MAX_DEP_TIER', '2')), changes)
            lines = '\n'.join(f'{key}={json.dumps(value)}' for key, value in outputs.items())
            print(lines)
            if os.environ.get('GITHUB_OUTPUT'):
                with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
                    output.write(lines + '\n')
        elif sys.argv[1] == 'order':
            print('\n'.join(order(root, *sys.argv[2:])))
        elif sys.argv[1] == 'download':
            download(root, *sys.argv[2:])
        elif sys.argv[1] == 'stage':
            stage(root, *sys.argv[2:])
        elif sys.argv[1] == 'pins':
            print(' '.join(pins(root, *sys.argv[2:])))
        else:
            check(root, *sys.argv[1:])
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(f'::error::{error}')
