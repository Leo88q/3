#!/usr/bin/env python3
# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
"""Apply reviewed engine files to an exact upstream revision, never to arbitrary edits."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT/'native'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def confined(root, relative):
    path = PurePosixPath(relative)
    if not relative or path.is_absolute() or '..' in path.parts or '\\' in relative:
        raise ValueError('Unsafe override path: '+relative)
    target = root/relative
    if target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError('Override path escapes root or is a symlink: '+relative)
    return target


def entries(native=NATIVE):
    doc=json.loads((native/'dependency-overrides.json').read_text())
    if doc.get('schema') != 1:
        raise ValueError('Unknown override schema')
    pins={d['path']:d['commit'] for d in json.loads((native/'upstream.lock.json').read_text())['dependencies']}
    seen=set()
    for item in doc['files']:
        key=(item['dependency'],item['path'])
        if key in seen: raise ValueError('Duplicate override target')
        seen.add(key)
        if pins.get('dependencies/'+item['dependency']) != item['commit']:
            raise ValueError('Override commit disagrees with upstream lock')
        source=confined(native/'overrides',item['dependency']+'/'+item['path'])
        if digest(source.read_bytes()) != item['sha256']:
            raise ValueError('Modified/unreviewed override source: '+str(source))
        yield item,source


def apply(native=NATIVE, check=False, only=None):
    pending=[]
    if only and only not in {item["dependency"] for item,_ in entries(native)}:
        raise ValueError("Unknown override dependency: "+only)
    # Validate the entire set before changing anything: one dirty target blocks all.
    for item,source in entries(native):
        if only and item["dependency"] != only: continue
        folder=confined(native/'zooshi/dependencies',item['dependency'])
        stamp=json.loads((folder/'.noriwake-source.json').read_text())
        if stamp.get('commit') != item['commit']:
            raise ValueError('Dependency commit mismatch: '+item['dependency'])
        source_ids={f['path']:f['sha'] for f in stamp['files']}
        if source_ids.get(item['path']) != item['upstream_blob_sha1']:
            raise ValueError('Original blob does not match reviewed override: '+item['path'])
        target=confined(folder,item['path'])
        data=target.read_bytes()
        if digest(data)==item['sha256']: continue
        if git_blob(data)!=item['upstream_blob_sha1']:
            raise ValueError('Refusing to overwrite local engine edit: '+item['path'])
        if check: raise ValueError('Engine override not applied: '+item['path'])
        pending.append((source,target))
    for source,target in pending:
        temp=target.with_name(target.name+'.noriwake-tmp')
        if temp.exists() or temp.is_symlink(): raise ValueError('Temporary override path already exists')
        try:
            # Exclusive creation prevents clobbering other files or following symlinks.
            with temp.open('xb') as stream: stream.write(source.read_bytes())
            temp.chmod(target.stat().st_mode & 0o777)
            os.replace(temp,target)
        finally:
            temp.unlink(missing_ok=True)
    print('Engine overrides verified.' if check else f'Engine overrides: applied {len(pending)} file(s); safe to repeat.')
