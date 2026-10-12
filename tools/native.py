#!/usr/bin/env python3
"""Pinned source-fork preparation. No shell scripts from upstream are executed."""
# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
# See native/zooshi/LICENSE.
import argparse
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT/'tools') not in sys.path: sys.path.insert(0,str(ROOT/'tools'))
NATIVE = ROOT / 'native'
GAME = NATIVE / 'zooshi'
CACHE = ROOT / '.cache' / 'zooshi'


def blob_hash(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def safe_path(root, relative):
    part = PurePosixPath(relative)
    if part.is_absolute() or '..' in part.parts or '\\' in relative:
        raise ValueError('Unsafe path: ' + relative)
    path = root / relative
    # Check parents, not the final file: upstream contains documented symlinks.
    if not path.parent.resolve().is_relative_to(root.resolve()):
        raise ValueError('Symlink escapes destination: ' + relative)
    return path


def read_blob(path):
    return os.readlink(path).encode() if path.is_symlink() else path.read_bytes()


def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.part')
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Noriwake-source-preparation'})
        with urllib.request.urlopen(request, timeout=90) as response, temporary.open('wb') as out:
            shutil.copyfileobj(response, out)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def hydrate(lock, offline=False):
    entries = [f for f in lock['files'] if f['storage'] == 'external']
    needed = [f for f in entries if not safe_path(GAME, f['path']).exists()]
    # Never silently overwrite a modified art source.
    for f in entries:
        path = safe_path(GAME, f['path'])
        if path.is_symlink():
            raise ValueError('External assets cannot be symlinks: ' + f['path'])
        if path.exists() and blob_hash(read_blob(path)) != f['git_blob_sha1']:
            raise ValueError('Modified external asset; refusing overwrite: ' + f['path'])
    if not needed:
        print('All external assets already verified.'); return
    archive = CACHE / 'upstream.tar.gz'
    if not archive.exists():
        if offline:
            raise ValueError('No cached archive. Run assets without --offline on a networked machine.')
        download(f"https://codeload.github.com/google/zooshi/tar.gz/{lock['commit']}", archive)
    # Git blob IDs below are authoritative even if GitHub regenerates gzip headers.
    print('Archive SHA256:', hashlib.sha256(archive.read_bytes()).hexdigest())
    with tarfile.open(archive, 'r:gz') as tar:
        for f in needed:
            member = tar.getmember('zooshi-' + lock['commit'] + '/' + f['path'])
            if not member.isfile() or member.size != f['size']:
                raise ValueError('Unexpected archive member: ' + f['path'])
            data = tar.extractfile(member).read()
            if blob_hash(data) != f['git_blob_sha1']:
                raise ValueError('Git blob hash mismatch: ' + f['path'])
            target = safe_path(GAME, f['path'])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    print(f'Restored and verified {len(needed)} assets. Cloud config was NOT restored.')


def verify(lock, assets=False):
    modifications = json.loads((NATIVE / 'modifications.json').read_text())
    errors = []
    entries = {f['path']: f for f in lock['files']}
    for p in modifications:
        if p not in entries:
            errors.append('Unrecognized modified upstream path: ' + p)
    for f in lock['files']:
        if f['storage'] != 'tracked' and not (assets and f['storage'] == 'external'):
            continue
        path = safe_path(GAME, f['path'])
        if not path.exists():
            errors.append('Missing: ' + f['path']); continue
        data = read_blob(path)
        if f['path'] in modifications:
            expected = modifications[f['path']]['sha256']
            if hashlib.sha256(data).hexdigest() != expected:
                errors.append('Unrecorded downstream edit: ' + f['path'])
        elif blob_hash(data) != f['git_blob_sha1']:
            errors.append('Unrecorded upstream edit: ' + f['path'])
    if errors:
        raise ValueError('\n'.join(errors))
    mirrors = json.loads((NATIVE/'dependency-mirrors.json').read_text())
    for name in mirrors['mirrors']:
        match = [d for d in lock['dependencies'] if d['path'] == 'dependencies/'+name]
        if len(match) != 1: raise ValueError('Unknown mirror dependency: '+name)
        dependency_repository(match[0])
    import engine_overrides
    list(engine_overrides.entries(NATIVE))
    print('Provenance verified: upstream blobs, downstream changes and engine override sources.')


def dependency_repository(d):
    name = d['path'].split('/')[-1]
    url = d['url'].replace('http://github.com/', 'https://github.com/').removesuffix('.git')
    mirrors=json.loads((NATIVE/'dependency-mirrors.json').read_text())
    if mirrors.get('schema')!=1: raise ValueError('Unknown mirror schema')
    mirror=mirrors['mirrors'].get(name)
    if mirror:
        if mirror['commit']!=d['commit'] or mirror['upstream_url']!=d['url']:
            raise ValueError('Reviewed mirror disagrees with immutable upstream pin')
        url='https://github.com/'+mirror['repository']
    if not url.startswith('https://github.com/'):
        raise ValueError('Non-GitHub upstream needs a reviewed mirror; no silent version substitution: ' + url)
    repo = url.removeprefix('https://github.com/')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        raise ValueError('Invalid GitHub repository')
    return url, repo


def fetch_dependency(lock, name):
    matches = [d for d in lock['dependencies'] if d['path'] == 'dependencies/' + name]
    if len(matches) != 1:
        raise ValueError('Unknown dependency: ' + name)
    d = matches[0]
    url, repo = dependency_repository(d)
    dest = safe_path(GAME, d['path'])
    if dest.exists() and any(dest.iterdir()):
        raise ValueError('Dependency directory already populated; refusing overwrite: ' + name)
    # Use GitHub tree IDs to verify *every* downloaded blob at the pinned commit.
    response = subprocess.run(['gh', 'api', f"repos/{repo}/git/trees/{d['commit']}?recursive=1"], check=True, capture_output=True, text=True)
    tree = json.loads(response.stdout)
    if tree.get('truncated'):
        raise ValueError('Truncated dependency tree; refusing partial verification.')
    archive = CACHE / f"{name}-{d['commit']}.tar.gz"
    if not archive.exists():
        download(f"https://codeload.github.com/{repo}/tar.gz/{d['commit']}", archive)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
        stage = Path(tmp)
        with tarfile.open(archive, 'r:gz') as tar:
            prefix = tar.getmembers()[0].name.split('/')[0]
            for entry in tree['tree']:
                if entry['type'] != 'blob':
                    continue
                is_link = entry['mode'] == '120000'
                try:
                    member = tar.getmember(prefix + '/' + entry['path'])
                except KeyError:
                    # git archive honors export-ignore, but our source manifest covers
                    # every Git blob. Retrieve the omitted object, never silently skip it.
                    data = subprocess.run(['gh','api','-H','Accept: application/vnd.github.raw+json',
                        f"repos/{repo}/git/blobs/{entry['sha']}"], check=True, capture_output=True).stdout
                else:
                    if not (member.issym() if is_link else member.isfile()):
                        raise ValueError('Unexpected dependency archive member: ' + entry['path'])
                    data = member.linkname.encode() if is_link else tar.extractfile(member).read()
                if blob_hash(data) != entry['sha']:
                    raise ValueError('Dependency blob mismatch: ' + entry['path'])
                path = safe_path(stage, entry['path']); path.parent.mkdir(parents=True, exist_ok=True)
                if is_link:
                    target = path.parent / data.decode()
                    if not target.resolve().is_relative_to(stage.resolve()):
                        raise ValueError('Escaping dependency symlink: ' + entry['path'])
                    path.symlink_to(data.decode())
                else:
                    path.write_bytes(data); path.chmod(int(entry['mode'][-3:], 8))
        if dest.exists(): dest.rmdir()  # Only the empty dependency directory, never the repository.
        shutil.copytree(stage, dest, symlinks=True)
    nested = [e for e in tree['tree'] if e['type'] == 'commit']
    (dest / '.noriwake-source.json').write_text(json.dumps({'commit':d['commit'], 'repository':url, 'nested_gitlinks':nested, 'files':[e for e in tree['tree'] if e['type']=='blob']}, indent=2))
    print(f"Verified {name} at {d['commit']}; {len(nested)} nested gitlinks NOT fetched.")


def doctor(lock):
    import engine_overrides
    approved={(e['dependency'],e['path']):e for e,_ in engine_overrides.entries(NATIVE)}
    problems = []
    try:
        engine_overrides.apply(NATIVE, check=True)
    except (ValueError,OSError) as exc:
        problems.append('Engine overrides not ready: '+str(exc))
    for tool in ['java', 'javac', 'cmake', 'ninja', 'python2']:
        cached_tools = {
            'cmake': ROOT/'.cache/host-tools/cmake/data/bin/cmake',
            'ninja': ROOT/'.cache/host-tools/bin/ninja',
            'java': ROOT/'.cache/java-tools/jdk4py/java-runtime/bin/java',
        }
        location = shutil.which(tool)
        cached = cached_tools.get(tool)
        if not location and cached and cached.is_file():
            location = str(cached)
        print(f"{tool}: {location or 'MISSING'}")
        if not location: problems.append('Tool absent: ' + tool)
    sdk = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    print('Android SDK:', sdk or 'NOT CONFIGURED')
    if not sdk or not Path(sdk).is_dir(): problems.append('Android SDK not configured')
    for d in lock['dependencies']:
        if d['path']=='dependencies/cardboard-java':
            print('cardboard-java: inactive in the touch build (upstream pin retained).')
            continue
        folder = GAME / d['path']
        stamp = folder / '.noriwake-source.json'
        if not stamp.exists(): problems.append('Unprepared dependency: ' + d['path']); continue
        data = json.loads(stamp.read_text())
        if data.get('commit') != d['commit']:
            problems.append('Wrong dependency commit: ' + d['path']); continue
        for entry in data.get('files', []):
            path = safe_path(folder, entry['path'])
            override=approved.get((folder.name,entry['path']))
            if not path.exists():
                problems.append('Dependency missing: '+str(path.relative_to(ROOT)))
            elif override and override['upstream_blob_sha1']==entry['sha'] and hashlib.sha256(read_blob(path)).hexdigest()==override['sha256']:
                pass
            elif blob_hash(read_blob(path)) != entry['sha']:
                problems.append('Dependency changed without review: '+str(path.relative_to(ROOT)))
        if data.get('nested_gitlinks'):
            problems.append('Nested dependencies unresolved: ' + d['path'])
    missing = sum(not (GAME/f['path']).exists() for f in lock['files'] if f['storage']=='external')
    if missing: problems.append(f'{missing} external art/audio assets missing: run assets')
    problems += [
        'AGP 8.7.3 / Gradle 8.11.1 / NDK r28c configuration prepared; full Gradle/NDK build NOT validated.',
        '64-bit libc++/VR=0 build paths prepared; engine and remaining legacy dependencies NOT compiled/linked.',
        'Offline providers compiled/tested, but full engine linkage and merged APK manifest audit are pending.',
        'Host asset checks are separate; Android resource packaging and native dependency linkage still need validation.',
        'APK and device tests are NOT completed.',
    ]
    print('\nBUILD BLOCKED (not a successful build):\n- ' + '\n- '.join(problems))
    return 1


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['assets','verify','deps','patches','doctor'])
    p.add_argument('--check',action='store_true',help='Check applied engine overrides without writing')
    p.add_argument('--offline',action='store_true')
    p.add_argument('--assets',action='store_true',help='Also verify hydrated binary assets')
    p.add_argument('--only',help='Select one dependency for deps or patches')
    args=p.parse_args()
    lock=json.loads((NATIVE/'upstream.lock.json').read_text())
    try:
        if args.command=='assets': hydrate(lock,args.offline)
        elif args.command=='verify': verify(lock,args.assets)
        elif args.command=='doctor': return doctor(lock)
        elif args.command=='patches':
            import engine_overrides
            engine_overrides.apply(NATIVE, check=args.check, only=args.only)
        elif args.only: fetch_dependency(lock,args.only)
        else:
            for d in lock['dependencies']: print(d['path'],d['commit'],d['url'])
    except (ValueError,OSError,KeyError,subprocess.CalledProcessError) as exc:
        print('ERROR:',exc,file=sys.stderr); return 1
    return 0

if __name__=='__main__': sys.exit(main())
