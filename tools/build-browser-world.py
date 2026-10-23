#!/usr/bin/env python3
"""Build the real browser world host from the pinned engine plus tracked patches."""
import hashlib
import gzip
import argparse
import importlib.util
import json
import re
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=ROOT/'.runtime/browser-world')
args=parser.parse_args()
out=args.output.resolve()
source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
spec=importlib.util.spec_from_file_location('browser_engine',ROOT/'tools/prepare-browser-engine.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
engine=module.prepare()
# The SDK engine shares bin/ between Debug/Release. Rebuild so a prior style
# check cannot leave Debug DLLs masquerading as an incremental Release output.
subprocess.run(['dotnet','build','browser/Frontier.Web','-t:Rebuild','-c','Release','-warnaserror','-p:BrowserEngineRoot='+str(engine),'-p:WasmAppDir='+str(out)],cwd=ROOT,check=True)
for source in (ROOT/'browser/Frontier.Web/wwwroot').rglob('*'):
    if source.is_file():
        target=out/source.relative_to(ROOT/'browser/Frontier.Web/wwwroot')
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
(out/'index.html').write_text((out/'index.html').read_text().replace('__SOURCE_COMMIT__',source_commit))
sources=[]
for directory,prefix in [(ROOT/'mods/frontier','mods/frontier'),(ROOT/'engine/mods/common','mods/common'),(ROOT/'browser/glsl','glsl')]:
    sources.extend((p,prefix+'/'+p.relative_to(directory).as_posix()) for p in directory.rglob('*') if p.is_file())
sources.append((ROOT/'engine/VERSION','VERSION'))
previous_manifest=out/'content-manifest.json'
new_paths={path for _,path in sources}
if previous_manifest.exists():
    for entry in json.loads(previous_manifest.read_text())['files']:
        if entry['path'] not in new_paths:
            stale=out/'content'/entry['path']
            if stale.exists():
                assert hashlib.sha256(stale.read_bytes()).hexdigest()==entry['sha256'],'Edited generated content preserved: '+str(stale)
                stale.unlink()
                parent=stale.parent
                while parent!=out/'content' and not any(parent.iterdir()):
                    parent.rmdir();parent=parent.parent
files=[]
for source,path in sources:
    target=out/'content'/path
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,target)
    if path=='mods/common/chrome/ingame-menu.yaml':
        # Local browser play has no desktop settings, file browser or menu lobby.
        menu,count=re.subn(r'(?m)^(\s*Buttons:).+$',r'\1 RESUME, SURRENDER, RESTART',target.read_text())
        assert count==1,'Unexpected pinned in-game menu format'
        target.write_text(menu)
    files.append({'path':path,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
(out/'content-manifest.json').write_text(json.dumps({'files':files},indent=2)+'\n')
for directory,prefix in [(ROOT/'licenses','licenses'), (ROOT/'browser/licenses','licenses/browser')]:
    for source in directory.rglob('*'):
        if source.is_file():
            target=out/prefix/source.relative_to(directory)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
shutil.copyfile(ROOT/'COPYING',out/'COPYING')
for name in ('platform-imports.json','upstream-sources.json'):
    shutil.copyfile(ROOT/'browser'/name,out/name)
bundle=sorted(p for p in out.rglob('*') if p.is_file() and p.name!='world-build.json')
largest=max(bundle,key=lambda p:p.stat().st_size)
report={
    'sourceCommit':source_commit,
    'sourceDirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
    'engineCommit':'524b6abdf1874b0132a7b06c1f89c7012f60124c',
    'patchDigest':json.loads((engine/'.browser-source.json').read_text())['patchDigest'],
    'files':len(bundle),'rawBytes':sum(p.stat().st_size for p in bundle),
    'gzipBytes':sum(len(gzip.compress(p.read_bytes(),mtime=0)) for p in bundle),
    'largestFile':largest.relative_to(out).as_posix(),'largestFileBytes':largest.stat().st_size,
    'cfStaticAssetLimitBytes':25*1024*1024,
    'assemblySha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'_framework').glob('OpenRA*.wasm')},
    'contentManifestSha256':hashlib.sha256((out/'content-manifest.json').read_bytes()).hexdigest(),
}
assert report['largestFileBytes']<=report['cfStaticAssetLimitBytes'],'CF static file size limit exceeded'
(out/'world-build.json').write_text(json.dumps(report,indent=2)+'\n')
print('Staged',len(files),'files for the actual Frontier browser world at',out)
print(json.dumps(report,indent=2))
