#!/usr/bin/env python3
"""Check browser rules/assets with OpenRA's .NET 8 command-line utility.
This is a developer lint tool, not a native game application.
"""
import importlib.util
import argparse
import os
from pathlib import Path
import subprocess
import shutil

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bundle', type=Path, default=ROOT/'.runtime/browser-world')
args = parser.parse_args()
content = args.bundle.resolve()/'content'
spec = importlib.util.spec_from_file_location('browser_engine', ROOT/'tools/prepare-browser-engine.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
engine = module.prepare()
subprocess.run(['dotnet', 'build', 'browser/OpenRA.Mods.Frontier.Web', '-c', 'Release', '-warnaserror',
                '-p:BrowserEngineRoot='+str(engine)], cwd=ROOT, check=True)
subprocess.run(['dotnet', 'build', str(engine/'OpenRA.Utility'), '-c', 'Release', '-warnaserror'], cwd=ROOT, check=True)
shutil.copyfile(ROOT/'browser/OpenRA.Mods.Frontier.Web/bin/Release/net8.0/OpenRA.Mods.Frontier.dll',
                engine/'bin/OpenRA.Mods.Frontier.dll')
# Inspect the staged browser content, including the adapted in-game menu.
environment = dict(os.environ, ENGINE_DIR=str(content),
                   MOD_SEARCH_PATHS=str(content/'mods'),
                   TREAT_WARNINGS_AS_ERRORS='true',
                   XDG_CONFIG_HOME=str(ROOT/'.runtime/browser-lint-config'))
subprocess.run(['python3', 'tools/test-content.py'], cwd=ROOT, check=True)
for check in ('--check-yaml', '--check-frontier-sprites', '--check-explicit-interfaces',
              '--check-conditional-trait-interface-overrides'):
    subprocess.run(['dotnet', str(engine/'bin/OpenRA.Utility.dll'), 'frontier', check],
                   cwd=ROOT, env=environment, check=True)
