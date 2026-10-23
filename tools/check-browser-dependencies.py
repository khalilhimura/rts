#!/usr/bin/env python3
"""Audit the browser host's resolved direct and transitive NuGet dependencies."""
import json
import importlib.util
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
project = ROOT/'browser/Frontier.Web/Frontier.Web.csproj'
spec = importlib.util.spec_from_file_location('browser_engine', ROOT/'tools/prepare-browser-engine.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
environment = dict(os.environ, BrowserEngineRoot=str(module.prepare()))
result = subprocess.run(['dotnet', 'list', str(project), 'package', '--vulnerable',
                         '--include-transitive', '--format', 'json'],
                        cwd=ROOT, env=environment, text=True, capture_output=True, check=True)
report = json.loads(result.stdout)
out = ROOT/'.runtime/browser-world-evidence'
out.mkdir(exist_ok=True)
(out/'dependency-audit.json').write_text(json.dumps(report, indent=2)+'\n')
assert report.get('version') == 1 and len(report.get('projects', [])) == 1, 'Incomplete browser audit'
assert not report.get('problems') and not report.get('messages'), 'NuGet audit reported problems'
for item in report['projects']:
    # NuGet omits frameworks entirely when --vulnerable finds no advisories.
    for framework in item.get('frameworks', []):
        for group in ('topLevelPackages', 'transitivePackages'):
            for package in framework.get(group, []):
                assert not package.get('vulnerabilities'), 'Vulnerable browser dependency: '+package['id']
inventory_result = subprocess.run(['dotnet', 'list', str(project), 'package',
                                   '--include-transitive', '--format', 'json'],
                                  cwd=ROOT, env=environment, text=True, capture_output=True, check=True)
inventory = json.loads(inventory_result.stdout)
(out/'dependency-inventory.json').write_text(json.dumps(inventory, indent=2)+'\n')
assert inventory.get('version') == 1 and len(inventory.get('projects', [])) == 1, 'Incomplete browser inventory'
assert not inventory.get('problems') and not inventory.get('messages'), 'NuGet inventory reported problems'
frameworks = inventory['projects'][0].get('frameworks', [])
assert any(f.get('framework') == 'net8.0' for f in frameworks), 'Missing browser target framework'
assert any(p['id'] == 'NuGet.CommandLine' and p['resolvedVersion'] == '6.12.5'
           for f in frameworks for group in ('topLevelPackages', 'transitivePackages')
           for p in f.get(group, [])), 'Patched NuGet client missing from the browser inventory'
assets = json.loads((project.parent/'obj/project.assets.json').read_text())
versions = [key for key in assets['libraries'] if key.startswith('NuGet.CommandLine/')]
assert versions == ['NuGet.CommandLine/6.12.5'], 'Browser must resolve patched NuGet.CommandLine: '+str(versions)
print('PASS: browser direct/transitive audit; no known advisories; NuGet.CommandLine 6.12.5 resolved')
