#!/bin/sh
# Start a local skirmish against Pioneer AI. No public server registration.
set -eu
cd "$(dirname "$0")"
mkdir -p .runtime
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$PWD/.runtime/config}"
exec ./launch-game.sh "Engine.SupportDir=$PWD/.runtime" Launch.Skirmish=true "$@"
