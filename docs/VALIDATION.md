# Browser validation — 2026-10-23

The selected `rts` environment was verified as `https://github.com/khalilhimura/rts.git` before editing. No AGENTS.md or local skills were present. Source work stays on `feat/browser-wasm-spike` and draft PR #1 until acceptance and hosted checks are green.

## First complete browser match

The actual OpenRA Salt Basin world, renderer, HUD, original assets/fonts and Pioneer AI ran in Chromium 154.0.8037.57 with headless SwiftShader on Debian 13. Input used real Playwright canvas events; diagnostic state exports were read-only. No game state was injected or game speed altered.

Selection passed at tick 118; movement at 142; generator placed at 332; refinery at 616; fabricator at 956; all three combat vehicles produced at 1,654; both economies delivered salvage at 1,663. Decisive win/loss passed at tick 4,842. The final snapshot at 4,848 recorded human Lost / AI Won, 5 / 10 kills, and 7,200 / 17,600 credits harvested. See `browser/evidence/first-world-acceptance.json` and `world-economy.png`.

This first run took approximately 27 minutes, roughly 3 simulation ticks per wall second versus the configured 25. It included software rendering and an inefficient original driver polling the entire history. The driver now polls only current observations and keeps its own history; client metrics separately record elapsed time, simulation ticks/second and step-call durations. These are functional headless checks, not human usability or representative GPU performance measurements.

## Browser-only validation

After that gameplay gate, native app launchers, packaging, solution/project entrypoints, .NET 6 build workflows and native-product documentation were removed. Shared engine/mod source and Git history remain. The unused NuGet executable dependency was removed from the browser graph, replacing its earlier 6.12.5 override. Audit regression tests still reject vulnerable transitive packages, incomplete reports and a reintroduced desktop NuGet client.

The current pipeline builds only .NET 8 browser code plus a developer console utility. It checks all original source/content/acquisition invariants, full rules/Fluent references, actual sprite decoding and interface contracts. Strict Debug builds enable code-style checking and warnings as errors; Release rebuilds prevent shared engine/bin output from retaining Debug binaries. The compatibility probe retains exact RGBA GPU readback and scaled pointer checks. Full gameplay, scaled input/focus, restart/context-loss and `/rts/` hosting assertions remain required.

Local strict Debug, Release, dependency and content checks passed at earlier browser milestones; browser-only exact-head results must be checked from their actual run. Final hosted status and artifact identity remain pending until recorded. No Cloudflare deployment has been made. Earlier Cloudflare API calls were blocked by proxy HTTP 403 and were not retried or bypassed.

The recoverable desktop baseline is Git commit `70a1ff084e9ff5557bab26c17f1588cd678293ae`; its historical evidence and instructions remain in that history, not the active product tree.
