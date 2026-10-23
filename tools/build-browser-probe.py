#!/usr/bin/env python3
"""Build the isolated managed OpenRA browser probe, never deploy it."""
import argparse
import importlib.util
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'.runtime/browser-probe'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--skip-engine-build', action='store_true')
args = parser.parse_args()
if not args.skip_engine_build:
    subprocess.run(['python3','tools/build-browser-world.py'], cwd=ROOT, check=True)
spec=importlib.util.spec_from_file_location('browser_engine',ROOT/'tools/prepare-browser-engine.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
engine=module.prepare()
subprocess.run(['dotnet','build','browser/Frontier.Browser.Probe','-c','Release','-warnaserror','-p:BrowserEngineRoot='+str(engine)],cwd=ROOT,check=True)
for source in (ROOT/'browser/Frontier.Browser.Probe/wwwroot').rglob('*'):
    if source.is_file(): shutil.copyfile(source,OUT/source.name)
content = OUT/'content'
content.mkdir(exist_ok=True)
sources = {
    'actors.yaml': 'mods/frontier/rules/actors.yaml',
    'map.yaml': 'mods/frontier/maps/salt-basin/map.yaml',
    'scout.png': 'mods/frontier/sequences/assets/scout.png',
}
for name, source in sources.items():
    shutil.copyfile(ROOT/source, content/name)
shutil.copyfile(ROOT/'COPYING', OUT/'COPYING')
shutil.copyfile(ROOT/'licenses/ORIGINAL-ASSETS.txt', OUT/'ORIGINAL-ASSETS.txt')
shutil.copyfile(ROOT/'licenses/PixVoxel-CC0-1.0.txt', OUT/'PixVoxel-CC0-1.0.txt')
files = list(p for p in OUT.rglob('*') if p.is_file() and p.name != 'probe-build.json')
largest = max(files, key=lambda p: p.stat().st_size)
report = {
    'playable': False,
    'measurementsExclude': ['probe-build.json'],
    'engineCommit': '524b6abdf1874b0132a7b06c1f89c7012f60124c',
    'files': len(files), 'rawBytes': sum(p.stat().st_size for p in files),
    'gzipBytes': sum(len(gzip.compress(p.read_bytes(), mtime=0)) for p in files),
    'largestFile': str(largest.relative_to(OUT)), 'largestFileBytes': largest.stat().st_size,
    'cfStaticAssetLimitBytes': 25*1024*1024,
    'assetSource': 'https://opengameart.org/content/pixvoxel-colorful-isometric-wargame-sprites',
    'contentSha256': {name: hashlib.sha256((content/name).read_bytes()).hexdigest() for name in sources},
    'assemblySha256': {name: hashlib.sha256((engine/'bin'/name).read_bytes()).hexdigest()
                       for name in ('OpenRA.Game.dll', 'OpenRA.Mods.Common.dll')},
}
assert report['largestFileBytes'] <= report['cfStaticAssetLimitBytes'], 'CF static file size limit exceeded'
(OUT/'probe-build.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
