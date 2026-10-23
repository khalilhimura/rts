# Browser-native port: first compatibility gate

**This branch contains a tested diagnostic, not a playable browser game.** The product direction is browser-only. Keep the working desktop baseline recoverable until browser gameplay passes the acceptance gate below; do not invest in native app packaging.

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

1. **Whole-world browser boot:** select/pin the browser runtime and platform source; keep the tested engine semantics or explicitly review a baseline migration. Track browser source/patches in Git. Stage the original mod, fonts, shaders and settings before initialization. Adapt `IPlatform`, GL bindings, font rasterization, the blocking game loop, background logging and filesystem assumptions. The existing `Platform` enum does not identify browser and its OS probe launches `uname`; `Log` starts a worker thread. Verify a real Frontier world and HUD render repeatedly with a responsive page. The public experimental fork's mod-loading hang is unresolved evidence, not a completed gate.
2. **Local simulation and AI:** adapt skirmish/session setup to OpenRA's existing `EchoConnection`, avoiding the desktop local TCP server and native sockets. Drive real world ticks from browser scheduling, preserve deterministic commands/randomness, and verify Pioneer AI construction and unit orders. This is a meaningful engine integration; a rendered sprite or ticking dummy loop cannot satisfy it.
3. **Playable parity:** automate real browser canvas input and observe selection, movement, all four structures, scout/tank/artillery production, both harvesting economies, projectiles/damage/kills, AI attacks and decisive win/loss. Test resize, context loss, focus/pause and restart. Compare recorded commands/state against the desktop baseline where applicable. No merge to main and no playable-deployment claim before this passes.
4. **Browser-only product:** remove desktop application entrypoints, packaging/workflows, desktop-only dependencies and documentation after gate 3, retaining shared browser-required code and history. Measure download size, memory, frame/tick timing on representative browsers; then deploy validated static files through the existing authorized Cloudflare path. No Worker is needed for single-player simulation. Native apps and multiplayer are deferred.

The first gate is the critical uncertainty. The tested probe eliminates several managed-code/asset/input questions, but does not establish the cost or performance of a complete world. This remains a multi-stage engine port, not an SDK export switch. [Rust assessment](../docs/RUST-ASSESSMENT.md) describes what to benchmark before considering a language change.
