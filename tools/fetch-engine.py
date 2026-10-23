#!/usr/bin/env python3
"""Fetch the hash-verified engine without overwriting an existing checkout.
Shared by the POSIX and PowerShell SDK entrypoints. GPL-3.0-or-later.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


def fetch(version, url, checksum, destination):
    destination = Path(destination).resolve()
    marker = {'version': version, 'url': url, 'sha256': checksum}
    receipt = destination / '.frontier-source.json'
    if destination.exists():
        if receipt.is_file() and json.loads(receipt.read_text()) == marker and (destination / 'VERSION').read_text().strip() == version:
            return
        raise RuntimeError(f'{destination} already exists without the expected source receipt. '
                           'Preserving it. Move it aside after reviewing any local changes, then rebuild.')
    with tempfile.TemporaryDirectory(prefix='.engine-fetch-', dir=destination.parent) as scratch:
        scratch = Path(scratch)
        archive = scratch / 'source.zip'
        subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error', url, '--output', str(archive)], check=True)
        actual = hashlib.sha256(archive.read_bytes()).hexdigest()
        if actual != checksum:
            raise RuntimeError(f'Engine SHA-256 mismatch: expected {checksum}, received {actual}. Nothing installed.')
        with zipfile.ZipFile(archive) as source:
            names = source.namelist()
            prefix = names[0].split('/')[0]
            for member in names:
                path = Path(member)
                if path.is_absolute() or '..' in path.parts or path.parts[0] != prefix:
                    raise RuntimeError('Unsafe archive path. Nothing installed.')
            source.extractall(scratch / 'unpacked')
        extracted = scratch / 'unpacked' / prefix
        # zip does not retain executable flags on extraction under Python.
        for script in extracted.rglob('*.sh'):
            script.chmod(script.stat().st_mode | 0o111)
        (extracted / 'VERSION').write_text(version + '\n')
        (extracted / '.frontier-source.json').write_text(json.dumps(marker, indent=2) + '\n')
        shutil.move(str(extracted), destination)
        print(f'Installed verified OpenRA {version} ({checksum}).')


if __name__ == '__main__':
    if len(sys.argv) != 5:
        sys.exit('Usage: fetch-engine.py VERSION URL SHA256 DESTINATION')
    try:
        fetch(*sys.argv[1:])
    except (OSError, RuntimeError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        sys.exit(str(error))
