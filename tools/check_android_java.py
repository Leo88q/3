#!/usr/bin/env python3
# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
"""Compile actual game/engine Java without VR SDK. Not a Gradle, JNI or APK build."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.cache/android-java-check'
# Test-only third-party binaries, not redistributed in the product/Git.
# GitHub mirrors are pinned by Git object identity, not a mutable branch.
TOOLS={
    'android-35.jar': ('Sable/android-platforms','2d6652edf0fb6046a23638f3a2f2c6246c745b08'),
    'jdt.jar': ('processing/processing4','b749e518b8a065856cc948363db71253fb855f84'),
}

def fetch(name):
    repo,sha=TOOLS[name]; path=CACHE/name
    if not path.exists():
        raise ValueError(f'Missing {path}; run with --fetch or provide --android-jar and installed javac.')
    data=path.read_bytes()
    actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if actual!=sha: raise ValueError('Test-tool Git blob mismatch: '+name)
    return path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fetch', action='store_true',help='Download/verify two pinned GitHub test-only JARs using gh')
    p.add_argument('--android-jar',type=Path,help='Official local Android SDK platform android.jar')
    p.add_argument('--javac',help='Use installed javac instead of cached Eclipse JDT')
    p.add_argument('--java',help='Java executable for cached JDT fallback')
    args=p.parse_args()
    if args.fetch:
        CACHE.mkdir(parents=True,exist_ok=True)
        for name,(repo,sha) in TOOLS.items():
            dest=CACHE/name
            if not dest.exists():
                # Download into a staging file; never retain failed/truncated output.
                with tempfile.TemporaryDirectory(dir=CACHE) as tmp:
                    candidate=Path(tmp)/name
                    with candidate.open('wb') as out:
                        subprocess.run(['gh','api','-H','Accept: application/vnd.github.raw+json',
                                        f'repos/{repo}/git/blobs/{sha}'],stdout=out,check=True)
                    data=candidate.read_bytes()
                    if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=sha:
                        raise ValueError('Downloaded test-tool identity mismatch')
                    os.replace(candidate,dest)
            fetch(name)
    import engine_overrides
    engine_overrides.apply(check=True, only='fplbase')
    android=args.android_jar or fetch('android-35.jar')
    if not android.is_file(): raise ValueError('android.jar does not exist')
    game=ROOT/'native/zooshi'; java_sources=sorted((game/'dependencies/fplbase/src_java').rglob('*.java'))
    java_sources+=sorted((game/'src_java/com/google/fpl/zooshi').rglob('*.java'))
    if len(java_sources)!=6: raise ValueError('Unexpected Java source set: review before changing test classpath')
    with tempfile.TemporaryDirectory(prefix='noriwake-java-') as output:
        common=['-source','1.8','-target','1.8','-bootclasspath',str(android),'-d',output,'-proc:none']
        javac=args.javac or shutil.which('javac')
        if javac:
            command=[javac,*common]
        else:
            java=args.java or shutil.which('java') or str(ROOT/'.cache/java-tools/jdk4py/java-runtime/bin/java')
            command=[java,'-cp',str(fetch('jdt.jar')),'org.eclipse.jdt.internal.compiler.batch.Main',*common]
        subprocess.run(command+[str(s) for s in java_sources],check=True)
        classes=list(Path(output).rglob('*.class'))
        if not classes: raise ValueError('Compiler produced no class files')
        print(f'Java-only compile passed: {len(java_sources)} real sources, {len(classes)} classes, no VR JARs.')
        print('NOT an APK build. JNI linkage, Android runtime/lifecycle, assets and native engine remain unverified.')

if __name__=='__main__':
    try: main()
    except (ValueError,OSError,subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc))
