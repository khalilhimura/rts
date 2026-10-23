#!/usr/bin/env python3
"""Strict Debug compilation of the browser host, platform, mod and patched engine."""
import importlib.util
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('browser_engine', ROOT/'tools/prepare-browser-engine.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
engine = module.prepare()
subprocess.run(['dotnet', 'build', 'browser/Frontier.Web', '-c', 'Debug', '-warnaserror',
                '-p:BrowserEngineRoot='+str(engine),
                '-p:WasmAppDir='+str(ROOT/'.runtime/browser-world-style'),
                '-p:EnforceCodeStyleInBuild=true', '-p:GenerateDocumentationFile=true'],
               cwd=ROOT, check=True)
