"""Publish the tested archives by digest; sign before moving public aliases."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def tags(release, latest, stream=None):
    core = re.sub(r'-r\d+$', '', release)
    aliases = [release, core]
    if stream and core != stream and not core.startswith(stream + '.'):
        raise ValueError(f'{release} does not belong to stream {stream}')
    depth = len(stream.split('.')) if stream else 1
    truncated = core
    while len(truncated.split('.')) > depth:
        truncated = truncated.rsplit('.', 1)[0]
        aliases.append(truncated)
    if latest:
        aliases.append('latest')
    return list(dict.fromkeys(aliases)), stream or (core.split('.')[0] if core[0].isdigit() else '')


def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.PIPE).strip()


def candidate(name, arch):
    return Path('out/artifacts') / f'release-{name}-{arch}.json'


def prepare(name, arch):
    import yaml
    root = Path('apps') / name
    metadata = json.loads((root / 'publish.json').read_text()) if (root / 'publish.json').exists() else {}
    repository = metadata.get('repository', name)
    if (root / 'melange.yaml').exists():
        package = yaml.safe_load((root / 'melange.yaml').read_text())['package']
        release = f"{package['version']}-r{package.get('epoch', 0)}"
    elif metadata.get('versionSourcePackage'):
        sbom = json.loads(Path(f'out/{name}-{arch}.spdx.json').read_text())
        versions = {p['versionInfo'] for p in sbom['packages'] if p['name'] == metadata['versionSourcePackage']}
        if len(versions) != 1:
            raise ValueError(f'Expected one SBOM version for {metadata["versionSourcePackage"]}: {versions}')
        release = versions.pop()
    else:
        release = 'latest'
    prefix, suffix = metadata.get('versionTrimPrefix', ''), metadata.get('versionTrimSuffix', '')
    if prefix:
        release = release.removeprefix(prefix)
    if suffix:
        release = release.removesuffix(suffix)
    if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}', release):
        raise ValueError(f'Invalid release tag: {release!r}')
    aliases, stream = tags(release, metadata.get('publishLatest', True), metadata.get('streamTag'))
    result = dict(sourceImage=name, repository=repository, releaseTag=release, arch=arch,
                  publishedTags=aliases, streamTag=stream, sourceCommit=os.environ.get('GITHUB_SHA'),
                  buildRun=os.environ.get('GITHUB_RUN_ID'), buildAttempt=os.environ.get('GITHUB_RUN_ATTEMPT'))
    candidate(name, arch).parent.mkdir(parents=True, exist_ok=True)
    candidate(name, arch).write_text(json.dumps(result))
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
        output.write(f'repository={repository}\n')


def push(name, arch):
    path = candidate(name, arch)
    data = json.loads(path.read_text())
    source = f"{os.environ['REGISTRY_NAMESPACE']}/{name}:candidate-{os.environ['GITHUB_RUN_ID']}-{os.environ['GITHUB_RUN_ATTEMPT']}"
    target = f"{os.environ['REGISTRY_NAMESPACE']}/{data['repository']}:candidate-{os.environ['GITHUB_RUN_ID']}-{os.environ['GITHUB_RUN_ATTEMPT']}-{arch}"
    run('docker', 'tag', source, target)
    print(run('docker', 'push', target))
    refs = json.loads(run('docker', 'image', 'inspect', '--format', '{{json .RepoDigests}}', target))
    repository = target.rsplit(':', 1)[0]
    matches = [ref for ref in refs if ref.rsplit('@', 1)[0] == repository]
    if len(matches) != 1:
        raise ValueError(f'Expected one pushed digest for {repository}: {matches}')
    data['imageRef'] = matches[0]
    path.write_text(json.dumps(data))


def report(name, arch):
    path = Path(f'cve-report-{name}-{arch}.json')
    data = json.loads(path.read_text())
    if not isinstance(data.get('matches'), list):
        raise ValueError('Invalid Grype report')
    metadata = json.loads(candidate(name, arch).read_text())
    with open(f'out/{name}-{arch}.tar', 'rb') as archive:
        metadata['archiveSHA256'] = hashlib.file_digest(archive, 'sha256').hexdigest()
    data['provenance'] = metadata
    path.write_text(json.dumps(data))


def publish(name):
    builds = [json.loads(candidate(name, arch).read_text()) for arch in ('x86_64', 'aarch64')]
    for field in ('sourceImage', 'repository', 'releaseTag', 'publishedTags', 'sourceCommit', 'buildRun', 'buildAttempt'):
        if builds[0][field] != builds[1][field]:
            raise ValueError(f'Architecture mismatch for {field}')
    for arch, build in zip(('x86_64', 'aarch64'), builds):
        if (build['arch'] != arch or build['buildRun'] != os.environ['GITHUB_RUN_ID']
                or build['buildAttempt'] != os.environ['GITHUB_RUN_ATTEMPT']
                or build['sourceCommit'] != os.environ['GITHUB_SHA']):
            raise ValueError('Candidate belongs to another build or architecture')
        expected = f"{os.environ['REGISTRY_NAMESPACE']}/{build['repository']}@sha256:"
        if not build.get('imageRef', '').startswith(expected) or not re.fullmatch(r'[0-9a-f]{64}', build['imageRef'][len(expected):]):
            raise ValueError('Missing or invalid tested image digest')
    release = builds[0]
    repository = f"{os.environ['REGISTRY_NAMESPACE']}/{release['repository']}"
    temporary = f"{repository}:candidate-{os.environ['GITHUB_RUN_ID']}-{os.environ['GITHUB_RUN_ATTEMPT']}"
    run('docker', 'buildx', 'imagetools', 'create', '--tag', temporary, *[b['imageRef'] for b in builds])
    manifest = json.loads(run('docker', 'buildx', 'imagetools', 'inspect', '--format', '{{json .Manifest}}', temporary))
    digest = manifest['digest']
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
        raise ValueError(f'Invalid published digest: {digest}')
    reference = f'{repository}@{digest}'
    run('cosign', 'sign', '--yes', reference)
    if release['releaseTag'] != 'latest':
        immutable = f"{repository}:{release['releaseTag']}-{digest[7:19]}"
        try:
            existing = json.loads(run('docker', 'buildx', 'imagetools', 'inspect', '--format', '{{json .Manifest}}', immutable))
        except subprocess.CalledProcessError as error:
            if not any(message in error.stderr.lower() for message in ('not found', 'manifest unknown', 'manifest_unknown')):
                raise
            run('docker', 'buildx', 'imagetools', 'create', '--tag', immutable, reference)
        else:
            if existing['digest'] != digest:
                raise ValueError(f'Immutable tag already points to another digest: {immutable}')
    for alias in sorted(release['publishedTags'], key=lambda tag: tag == 'latest'):
        run('docker', 'buildx', 'imagetools', 'create', '--tag', f'{repository}:{alias}', reference)
    Path(f'out/artifacts/published-{name}.json').write_text(json.dumps(dict(release, imageRef=reference)))


if __name__ == '__main__':
    try:
        {'prepare': prepare, 'push': push, 'report': report, 'publish': publish}[sys.argv[1]](*sys.argv[2:])
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(f'::error::{error}\n{getattr(error, "stderr", "")}')
