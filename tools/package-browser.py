#!/usr/bin/env python3
"""Package the fully tested browser game under rts/, without deploying anything."""
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
bundle = ROOT/'.runtime/browser-world'
build = json.loads((bundle/'world-build.json').read_text())
result = json.loads((ROOT/'.runtime/browser-world-evidence/validation-result.json').read_text())
assert result['status']=='passed' and result['gameplay'] and result['lifecycle'] and result['subpath']=='/rts/'
assert result['build']==build, 'Validation does not match this bundle'
assert not build['sourceDirty'], 'Commit the source before preparing a deployable artifact'
assert (bundle/'_framework/OpenRA.Game.wasm').is_file(), 'Actual engine missing'
assert (bundle/'content/mods/frontier/maps/salt-basin/map.bin').is_file(), 'Actual map missing'
target = ROOT/'.runtime/rts-site.zip'
with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for source in sorted(bundle.rglob('*')):
        assert not source.is_symlink(), 'Unexpected symlink in browser output'
        if source.is_file():
            archive.write(source, 'rts/'+source.relative_to(bundle).as_posix())
print('Prepared',target,'for https://thefutureissolo.com/rts/ at source',build['sourceCommit'])
