# Rust opportunities for the browser port

Recommendation: first obtain a functioning C#/.NET WASM world, profile it, then consider a small Rust kernel only if measured total browser cost improves. No Rust rewrite, dependency or toolchain has been introduced. Rust does not solve the currently missing WebGL/font/window/loop/session integration by itself.

| Candidate | Evidence in this checkout | Recommendation |
|---|---|---|
| Path search | `OpenRA.Mods.Common/Pathfinder` already separates graph/search types; `CellInfo` uses integer costs. However `HierarchicalPathFinder` and `PathSearch` depend on `World`, `Locomotor`, custom movement layers and dynamic actors. | Best first candidate if profiling shows a bottleneck. Batch requests over an explicit grid/cost snapshot; keep world/trait callbacks in C#. Do not cross the language boundary for each expanded node. |
| Asset decoding | `OpenRA.Game/FileFormats/Png.cs` is managed code and now decodes our actual eight-direction PNG in browser. The prototype's images are small, checked and known. | Low priority without measured stalls. Prefer staging/caching/offline preprocessing first. Rewriting decoders for unused legacy formats does not advance this original-content game. |
| Command validation / whole simulation | Production, movement, harvesting, AI, combat, ownership and win conditions span traits, orders and actors. `World.SyncHash()` includes actor sync values and shared random state. | A wholesale Rust simulation is a new engine effort with broad behavior/determinism risk. It is not an isolated port optimization. A narrow pure validation kernel may be considered later; an on-device validator alone is not multiplayer authority. |

## Boundary cost and integration

The diagnostic measured 10,000 warmed primitive JS/.NET calls in 7.8 ms in one local Chromium run. This excludes real payloads, serialization, additional Wasm modules and searches. It does not measure Rust or predict a speedup.

A separate Rust Wasm module generally needs an explicit buffer/ABI bridge and careful ownership/copy accounting. A statically linked C ABI may avoid routing every operation through JavaScript, but it introduces build/ABI constraints. [.NET's native Wasm integration](https://learn.microsoft.com/en-us/aspnet/core/blazor/webassembly-native-dependencies?view=aspnetcore-10.0) uses Emscripten-built native objects; the [Rust target documentation](https://doc.rust-lang.org/rustc/platform-support/wasm32-unknown-emscripten.html) warns that Emscripten versions and flags must agree. This is an integration option to prove, not an already-working bridge in this repository.

## Benchmark and correctness gate before any rewrite

1. Profile an actual Salt Basin browser match: p50/p95 simulation tick, rendering, path search, allocations, startup and peak memory. The current probe starts no world, so those measurements do not exist yet.
2. Record representative path-query batches and dynamic blocker/cost snapshots using the C# implementation. Include blocked/unreachable goals, equal-cost paths, groups, terrain speeds, moving blockers and cancellations.
3. After an explicit Rust decision, compare identical batches in C# WASM and Rust WASM. Include extraction, copies/marshalling, allocation and result integration in end-to-end latency; separately report kernel time, download size and memory. A faster inner loop that slows total ticks fails the performance gate.
4. Differentially verify path/cost results, deterministic tie-breaking, integer overflow behavior, order/iteration stability and the shared RNG sequence. Replay the same command stream and compare per-tick state hashes and final economy/combat outcomes across builds/browsers. Do not accept an approximately similar simulation in place of matching rules.

The first optimization decision should follow the whole-world profile. Full engine replacement requires a separate product/architecture decision and is not authorized by asking about opportunities.
