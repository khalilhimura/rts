# Browser build and validation

Frontier Collective runs the actual pinned OpenRA world, rendering, simulation, production and Pioneer AI through .NET WebAssembly/WebGL2. The first full Chromium match passed every gameplay gate through win/loss at tick 4,842 (final snapshot 4,848). Native app entrypoints/packaging were removed after that gate. Final browser-only and `/rts/` validation is in progress; nothing has been deployed.

## Build and run

Use SDK **8.0.426**, Python 3 and `patch`; .NET 6 and native SDL/OpenAL/FreeType are not required. Only the developer lint utility executes as a .NET 8 console tool.

```sh
dotnet workload install wasm-tools --skip-manifest-update
python3 -m pip install -r browser/requirements-test.txt
python3 -m playwright install chromium
python3 tools/build-browser-world.py
python3 -m http.server 8080 --bind 127.0.0.1 --directory .runtime/browser-world
```

Open `http://127.0.0.1:8080`. Left click/drag selects; right click moves/attacks. Build Generator → Refinery → Fabricator, then scout/tank/artillery. The refinery's crawler harvests automatically. Destroy opposing structures to win. The menu provides Resume/Restart; New skirmish reloads the page. The prototype is silent. Browser WebAssembly, WebGL2 and a secure context (HTTPS or localhost) are required.

`engine-source.json` pins the acquired engine commit/archive/hash. `prepare-browser-engine.py` applies tracked patches/additions to a separate hash-addressed copy, preserves unexpected source directories and rejects edits to generated source. Existing game logic/rules remain; EchoConnection carries local orders without a game server. Browser rule loading uses the existing synchronous path, static maps omit native watching, and unsupported GC compaction is skipped. Canvas FontFace uses the exact staged GNU FreeSans bytes; the fork's modified FreeType error handling was not adopted. No replacement simulation or remote desktop is included.

## Required checks

```sh
python3 tools/check-browser-content.py
python3 tools/check-browser-style.py
python3 tools/check-browser-dependencies.py
python3 tools/build-browser-probe.py --skip-engine-build
python3 tools/test-browser-probe.py
python3 tools/smoke-browser-world.py --full-gameplay
python3 tools/package-browser.py
```

For a focused end-game lifecycle check without repeating production/combat, run `python3 tools/smoke-browser-world.py --lifecycle-only`; it uses normal `/surrender` chat input and does not satisfy the full packaging gate. Restart checks observe visible button bounds, confirm the dialog, wait for the defeat UI transition and require a new page instance.

Select an installed Chromium with `--browser-path /path/to/chromium` on either browser test. The content check runs source/map/acquisition/audit regression tests, complete rules/Fluent lint, actual sprite-frame decoding and interface checks against staged browser content. Strict Debug compilation checks patched engine/platform/mod/host code with warnings as errors. Release rebuilds avoid stale shared Debug outputs. The dependency gate checks direct/transitive advisories, full resolved inventory and the absence of the unused desktop NuGet executable.

The compatibility probe remains a required diagnostic: inherited MiniYaml rules, reflection-based production trait loading, original PNG decoding, complete RGBA GPU readback and scaled pointer input. Its small shader/input sink is not the world renderer; full gameplay is separately required. It now references the same isolated .NET 8 engine as the world.

The full test serves only `/rts/`, redirects `/rts` to `/rts/`, blocks external requests and enforces a local CSP without inline script/style or general JavaScript eval. It drives real canvas/keyboard events and observes read-only engine state: selection/movement, all structures/units, both economies, combat/AI and decisive win/loss. Scaled input, focus release, the actual in-game restart and context-loss recovery are also checked. Tick budgets, wall limits and a 90-second stall detector bound waits. No game state or speed is changed to pass tests.

Evidence stays in ignored `.runtime/browser-world-evidence/`; published CI artifacts include snapshots, screenshots, dependency reports and client timing. `world-build.json` records exact source/assembly/content identities, download sizes and the 25 MiB file gate. `package-browser.py` accepts only a clean committed bundle with matching successful gameplay/lifecycle/subpath evidence; it creates `.runtime/rts-site.zip` containing **only `rts/`**. See [TFIS integration](../docs/TFIS-DEPLOYMENT.md).

## Measurements and limits

The first headless Chromium 154 / SwiftShader match took about 27 minutes, roughly 3 simulation ticks/second against the configured 25. It also included the original inefficient full-history polling driver, now corrected. This is a material limitation and is not representative GPU/browser usability evidence. The Release world bundle measured roughly 37.0 MB raw / 15.2 MB individually gzipped; its largest file was 4,199,705 bytes. Repeat measurements after pruning/optimization rather than treating this as a production download budget.

Historical probe evidence in `evidence/` recorded 956 / 4174 / 21 reflected types, 126.6 ms managed inspection, 1.1467 seconds total probe, and 7.8 ms for 10,000 warmed primitive interop calls. Those are diagnostic lower bounds, excluding world simulation, rendering, buffers and Rust. Current browser builds may have additional generated types. Profile before any [Rust decision](../docs/RUST-ASSESSMENT.md).

## Sources and scope

`platform-imports.json` pins imported GPL platform/input/GLSL files and original hashes; headers, COPYING and AUTHORS are retained in `licenses/`. [openra-wasm commit 424fb8b](https://github.com/Baronvonbonbon/openra-wasm/tree/424fb8b08d98de057015bc2cfcaddeaf10f3cc14) supplied reusable platform source, backported to the pinned engine rather than adopting its newer engine wholesale. Its mod-loading hang was traced here to waiting for background rule tasks on a single-thread runtime. No fork mods or retail archives were checked out or reused.

The Rosebud/OpenHV export was research only; corresponding modern reproducible source was not established, so its binaries/content were not adopted. User-supplied REA is an optional MIT Node/MCP inspection toolkit, not a port or compiler; it was inspected but never installed/executed. Exact findings/links are in `upstream-sources.json` and [provenance](../docs/PROVENANCE.md).

The active product is browser-only. Native apps, multiplayer, Lua campaigns, representative GPU performance work and production polish remain separate milestones. Shared engine source and recoverable history remain. Deployment at `thefutureissolo.com/rts/` still needs an authorized TFIS publishing path; the earlier environment proxy HTTP 403 was not retried or bypassed.
