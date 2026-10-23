#!/usr/bin/env python3
"""Audit the browser's resolved direct/transitive dependencies; fail closed."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def validate(report, assets, inventory):
    for label, data in [('audit', report), ('inventory', inventory)]:
        if data.get('version') != 1 or len(data.get('projects', [])) != 1:
            raise ValueError('Incomplete browser '+label)
        if data.get('problems') or data.get('messages'):
            raise ValueError('NuGet reported '+label+' problems')
    # --vulnerable omits frameworks when it finds no advisories.
    for project in report['projects']:
        for framework in project.get('frameworks', []):
            for group in ('topLevelPackages', 'transitivePackages'):
                for package in framework.get(group, []):
                    if package.get('vulnerabilities'):
                        raise ValueError('Vulnerable dependency: '+package['id'])
    frameworks = inventory['projects'][0].get('frameworks', [])
    if not any(f.get('framework') == 'net8.0' for f in frameworks):
        raise ValueError('Missing browser target framework')
    packages = [p for f in frameworks for group in ('topLevelPackages', 'transitivePackages') for p in f.get(group, [])]
    if not any(p['id'] == 'Newtonsoft.Json' and p['resolvedVersion'] == '13.0.3' for p in packages):
        raise ValueError('Missing resolved browser dependency inventory')
    # The desktop NuGet executable is unused by browser/Common C# and is removed.
    if any(p['id'] == 'NuGet.CommandLine' for p in packages) or any(k.startswith('NuGet.CommandLine/') for k in assets['libraries']):
        raise ValueError('Desktop NuGet.CommandLine must be absent from the browser graph')
    if 'Newtonsoft.Json/13.0.3' not in assets['libraries']:
        raise ValueError('Resolved assets disagree with browser inventory')


def main():
    spec = importlib.util.spec_from_file_location('browser_engine', ROOT/'tools/prepare-browser-engine.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    environment = dict(os.environ, BrowserEngineRoot=str(module.prepare()))
    project = ROOT/'browser/Frontier.Web/Frontier.Web.csproj'
    out = ROOT/'.runtime/browser-world-evidence'
    out.mkdir(exist_ok=True)
    reports = []
    for filename, options in [('dependency-audit.json', ['--vulnerable']), ('dependency-inventory.json', [])]:
        result = subprocess.run(['dotnet', 'list', str(project), 'package', *options, '--include-transitive', '--format', 'json'],
                                cwd=ROOT, env=environment, text=True, capture_output=True, check=True)
        data = json.loads(result.stdout)
        (out/filename).write_text(json.dumps(data, indent=2)+'\n')
        reports.append(data)
    assets = json.loads((project.parent/'obj/project.assets.json').read_text())
    validate(reports[0], assets, reports[1])
    print('PASS: browser direct/transitive audit; no known advisories; unused desktop NuGet executable absent')


if __name__ == '__main__':
    main()
