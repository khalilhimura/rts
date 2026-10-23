#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p .runtime
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$PWD/.runtime/config}"
python3 tools/test-content.py
TREAT_WARNINGS_AS_ERRORS=true ./utility.sh --check-yaml
./utility.sh --check-frontier-sprites
./utility.sh --check-explicit-interfaces
./utility.sh --check-conditional-trait-interface-overrides
