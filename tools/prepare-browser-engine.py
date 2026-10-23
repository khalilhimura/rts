#!/usr/bin/env python3
"""Prepare an isolated browser build of the verified engine; preserve desktop source.
Source edits live in reviewed patches/additions. Each patch digest gets a separate
generated directory, so changing a patch never destroys a previous build tree.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def prepare():
    baseline = ROOT/'engine'
    marker = json.loads((baseline/'.frontier-source.json').read_text())
    assert marker['sha256'] == '401b46b32ebddd04ea5ad342528195afe555d0800a7bbb5e07d00f3eb5b9e2ec', 'Unexpected engine baseline'
    patches = sorted((ROOT/'browser/engine-patches').glob('*.patch'))
    additions = sorted(p for p in (ROOT/'browser/engine-additions').rglob('*') if p.is_file())
    digest = hashlib.sha256(b''.join(p.read_bytes() for p in patches+additions)).hexdigest()[:12]
    out = ROOT/'.runtime'/('browser-engine-'+digest)
    stamp = out/'.browser-source.json'
    if stamp.exists():
        data = json.loads(stamp.read_text())
        for name, sha in data['sourceSha256'].items():
            if hashlib.sha256((out/name).read_bytes()).hexdigest() != sha:
                raise RuntimeError('Generated browser source was edited; preserving it: '+str(out/name))
        return out
    if out.exists():
        raise RuntimeError('Unmarked browser directory preserved: '+str(out))
    out.mkdir(parents=True)
    for name in ('OpenRA.Game', 'OpenRA.Mods.Common'):
        shutil.copytree(baseline/name, out/name, ignore=shutil.ignore_patterns('bin', 'obj'))
    for name in ('Directory.Build.props', 'COPYING', 'AUTHORS', 'VERSION', '.editorconfig'):
        if (baseline/name).exists():
            shutil.copyfile(baseline/name, out/name)
    for patch in patches:
        subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(patch)], cwd=out, check=True)
    for source in additions:
        target = out/source.relative_to(ROOT/'browser/engine-additions')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    source_hashes = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in out.rglob('*') if p.is_file()}
    stamp.write_text(json.dumps({'base': marker, 'patchDigest': digest, 'sourceSha256': source_hashes}, indent=2)+'\n')
    return out


if __name__ == '__main__':
    print(prepare())
