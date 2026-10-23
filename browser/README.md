# Browser-native port

This branch now contains the actual OpenRA browser world as well as the earlier compatibility diagnostic. Salt Basin, the HUD, original fonts/sprites, two-player simulation, Pioneer AI, selection, movement and building placement have run in Chromium. Full match acceptance and hosted validation are still in progress; this is not a deployed browser product. Keep the desktop baseline recoverable until the complete acceptance gate passes.

## Run the actual world

Use the pinned .NET SDK 8.0.426, its `wasm-tools` workload, Python 3, `curl`, and `patch`. The browser host and isolated engine copy target .NET 8; no native game process, socket server, SDL, OpenAL or FreeType is used by the browser host.

```sh
dotnet workload install wasm-tools --skip-manifest-update
python3 -m pip install -r browser/requirements-test.txt
python3 -m playwright install chromium
python3 tools/build-browser-world.py
python3 tools/check-browser-style.py
python3 tools/check-browser-dependencies.py
python3 tools/smoke-browser-world.py --full-gameplay
```

For manual play, serve `.runtime/browser-world/` on loopback, for example `python3 -m http.server 8080 --bind 127.0.0.1 --directory .runtime/browser-world`, and open `http://127.0.0.1:8080`. It immediately starts Salt Basin against Pioneer AI. Left click/drag selects; right click moves or attacks. Build Generator → Refinery → Fabricator, then queue vehicles. The refinery's crawler harvests automatically. Destroy opposing structures to win. The browser needs WebGL2 and WebAssembly, and a secure context (HTTPS or localhost) for integrity checks. The current prototype is silent.

`tools/prepare-browser-engine.py` applies the tracked patches and additions to a separate hash-addressed copy of the verified engine. It preserves `engine/` and rejects edits to generated source instead of overwriting them. `platform-imports.json` pins the imported GPL platform/input/GLSL files to their original hashes; their copyright headers, COPYING and AUTHORS are retained. The font backend rasterizes the exact staged GNU FreeSans bytes using browser Canvas. The fork's modified FreeType error handling was not adopted.

The browser loop executes the original engine's logic/render scheduling one step per animation callback. Existing `EchoConnection` carries local commands, and trait-defined lobby defaults configure the real world and AI. Rules load synchronously because the browser runtime is single-threaded; static map discovery has no native directory watcher; unsupported large-object-heap compaction is skipped. No replacement simulation is included. Lua campaigns and multiplayer are outside this single-map milestone.

The smoke test blocks requests outside its loopback origin and drives real canvas events; state exports only observe the actual engine. It checks tick progress with bounded waits. Evidence is written to `.runtime/browser-world-evidence/`, including console/state snapshots, screenshots and the dependency audit. `world-build.json` records content/assembly hashes, source-patch digest, download measurements and the 25 MiB per-file gate. Headless SwiftShader results establish functionality, not representative gameplay performance.

## Run the probe

Use the repository-pinned .NET SDK 8.0.426, .NET 6 runtime for compiling the existing engine, and Python 3. The probe itself executes on the browser's .NET 8.0.32 WebAssembly runtime. This is a compatibility baseline, not the final supported-runtime decision for the browser product.

```sh
dotnet workload install wasm-tools --skip-manifest-update
python3 -m pip install -r browser/requirements-test.txt
python3 -m playwright install chromium
python3 tools/build-browser-probe.py
python3 tools/test-browser-probe.py
```

An existing Chromium can be selected with `--browser-path /path/to/chromium`. The test serves files only on loopback, blocks browser requests outside that local origin, checks real WebAssembly resources loaded, and closes its server/browser afterward. To inspect manually, serve `.runtime/browser-probe/` with a local static server. No Cloudflare credentials or deployment are involved.

The build references the existing, pinned OpenRA.Game, OpenRA.Mods.Common and OpenRA.Mods.Frontier assemblies without modifying their source. Only the real Frontier actor YAML, Salt Basin metadata and CC0 scout sheet are staged. The probe verifies inherited MiniYaml rules, reflection-based production trait loading, OpenRA PNG decoding, full WebGL2 pixel readback and pointer coordinates at two CSS scales. Its WebGL diagnostic shader and input sink are small platform tests; they are not the engine's world renderer or live unit controls. No alternative simulation is included.

## Recorded local measurements

Chromium 154.0.8037.57, headless SwiftShader, loopback HTTP, one run on the selected Codex environment. These are diagnostic startup measurements, not network-delivery or gameplay performance claims.

| Measurement | Result |
|---|---:|
| OpenRA / Common / Frontier types reflected | 956 / 4174 / 21 |
| Reflection + inherited rules + trait + PNG inspection | 126.6 ms |
| Complete probe, including WebGL/readback and interop check | 1146.7 ms |
| 10,000 warmed primitive JS↔.NET calls | 7.8 ms |
| Bundle files / raw bytes | 214 / approximately 35.1 MB (excluding build report) |
| Sum of individually gzipped files | approximately 14.3 MB |
| Largest file | 4,199,705 bytes (`System.Private.CoreLib.wasm`) |

All eight scout directions were decoded and every RGBA byte matched GPU readback. Both right clicks reached OpenRA's `IInputHandler` as `(256,32,Right)`. The interop number is a lower-bound primitive round trip; it excludes buffers, JSON, Rust, path search, game state and threading. No Rust speedup follows from it.

Results, input/assembly hashes and a screenshot are in [evidence](evidence/). Repeat-run outputs remain in ignored `.runtime/browser-evidence/`. The build fails if any file exceeds Cloudflare's 25 MiB static-asset limit. The bundle is deliberately untrimmed because OpenRA depends heavily on reflection; trimming/AOT need separate correctness and download-size tests.

## Reusable-source findings

Exact inspected references and license evidence are recorded in [upstream-sources.json](upstream-sources.json).

* [Baronvonbonbon/openra-wasm at `424fb8b`](https://github.com/Baronvonbonbon/openra-wasm/tree/424fb8b08d98de057015bc2cfcaddeaf10f3cc14) has GPL-3.0-or-later source for a WebGL2 platform, DOM input, browser loop, FreeType integration and an Eluant/MoonSharp shim. It targets .NET 10 and a newer OpenRA tree. Its [startup script](https://github.com/Baronvonbonbon/openra-wasm/blob/424fb8b08d98de057015bc2cfcaddeaf10f3cc14/OpenRA.Web/wwwroot/main.js) explicitly labels full startup as hanging during mod loading. It is useful implementation research, not a verified drop-in port. Sparse source inspection excluded mods and game archives. No fork code or retail content was imported into this probe.
* [hakyong-tae/openhv-web](https://github.com/hakyong-tae/openhv-web) redistributes a Rosebud OpenHV static export. We inspected its README/NOTES, not its binary/content bundle. Its claimed port source, [openra-wasm-port/root](https://gitlab.com/openra-wasm-port/root), exposes branches last changed in July 2024; the inspected `prep-2307` commit targets net6.0/netstandard2.1 with a native SDL platform. Matching source/build instructions for the newer export were not established. Do not adopt that export as a reproducible corresponding-source baseline.
* [Rosebud's engineering account](https://rosebud.ai/engineering/porting-openra-to-the-browser) is evidence that the approach is feasible. Its desktop-assumption fixes help identify work; they do not supply a reproducible Frontier build by themselves.
* User-supplied [morluto/rea](https://github.com/morluto/rea) is a Node/TypeScript CLI and MCP inspection tool, not a game engine or browser compiler. We reviewed MIT license text, package 6.7.0, current commit metadata, managed-analysis source, WABT wrapper and CDP provider. It was actively updated on 2026-10-23; that is not an execution or quality certification. Its host-side filesystem/process integrations are development tools, not browser-game dependencies. It could audit managed native boundaries if needed; existing source inspection and Playwright cover this spike. It was not installed or executed. The environment's Node 24.19.0 also falls below its declared Node 24.22.1 minimum for that major line. Third-party licenses apply separately.

## Next gates

1. **Whole-world browser boot:** implemented locally with tracked platform sources/patches, original content, Canvas font rasterization and a nonblocking engine loop. The public fork's mod-loading hang was traced to synchronous waits for background rule-loading tasks; browser rule loading now uses the engine's existing synchronous path. Static map watching and unsupported GC compaction were adapted without changing game rules. Hosted exact-commit validation remains required.
2. **Local simulation and AI:** the actual `EchoConnection` session runs two players with trait-defined defaults and a fixed random seed. Pioneer AI has constructed its base and delivered salvage; both economies and all human combat vehicle production have been observed. Full combat acceptance remains in progress.
3. **Playable parity:** automate real browser canvas input and observe selection, movement, all four structures, scout/tank/artillery production, both harvesting economies, projectiles/damage/kills, AI attacks and decisive win/loss. Test resize, context loss, focus/pause and restart. Compare recorded commands/state against the desktop baseline where applicable. No merge to main and no playable-deployment claim before this passes.
4. **Browser-only product:** remove desktop application entrypoints, packaging/workflows, desktop-only dependencies and documentation after gate 3, retaining shared browser-required code and history. Measure download size, memory, frame/tick timing on representative browsers; then deploy validated static files through the existing authorized Cloudflare path. No Worker is needed for single-player simulation. Native apps and multiplayer are deferred.

The actual world clears the initial integration barrier, but complete gameplay, browser lifecycle handling and representative performance still need validation. This remains a multi-stage engine port. [Rust assessment](../docs/RUST-ASSESSMENT.md) describes what to benchmark before considering a language change.
