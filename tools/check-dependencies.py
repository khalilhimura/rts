#!/usr/bin/env python3
"""Fail CI on unresolved NuGet advisories, including transitive dependencies."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def validate(report, assets):
    if report.get('version') != 1 or len(report.get('projects', [])) < 3:
        raise ValueError('Incomplete NuGet vulnerability report')
    if report.get('problems') or report.get('messages'):
        raise ValueError('NuGet reported audit problems; inspect the JSON report')
    for project in report['projects']:
        for framework in project.get('frameworks', []):
            for group in ('topLevelPackages', 'transitivePackages'):
                for package in framework.get(group, []):
                    if package.get('vulnerabilities'):
                        raise ValueError(f"Vulnerable dependency: {package['id']} {package.get('resolvedVersion')}")
    versions = [key for key in assets['libraries'] if key.startswith('NuGet.CommandLine/')]
    if versions != ['NuGet.CommandLine/6.12.5']:
        raise ValueError(f'Expected patched NuGet.CommandLine/6.12.5, received {versions}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, help='Optional location for the original NuGet JSON report')
    args = parser.parse_args()
    command = ['dotnet', 'list', 'Frontier.sln', 'package', '--vulnerable', '--include-transitive', '--format', 'json']
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
    report = json.loads(result.stdout)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    assets = json.loads((ROOT/'engine/OpenRA.Mods.Common/obj/project.assets.json').read_text())
    validate(report, assets)
    print(f"PASS: {len(report['projects'])} projects audited including transitive dependencies; no known advisories; patched NuGet.CommandLine 6.12.5 resolved.")


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
