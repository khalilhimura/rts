#!/bin/sh
# Adapted from OpenRAModSDK (GPL-3.0-or-later), 2026-10-23.
# Share pinned acquisition with Windows; preserve pre-existing engine work.
set -eu
cd "$(dirname "$0")"
. ./mod.config
if [ -f ./user.config ]; then . ./user.config; fi
if [ "${AUTOMATIC_ENGINE_MANAGEMENT}" != True ]; then
    test "$(cat "$ENGINE_DIRECTORY/VERSION")" = "$ENGINE_VERSION"
    exit
fi
exec python3 tools/fetch-engine.py "$ENGINE_VERSION" "$AUTOMATIC_ENGINE_SOURCE" "$ENGINE_SOURCE_SHA256" "$ENGINE_DIRECTORY"
