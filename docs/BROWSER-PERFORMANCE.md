# Browser cursor and responsiveness

The deployed baseline (`e6428a8f2b9e5014e9c1ae0a311c10d9878849a0`) was reported slow in Brave on Mac, with two cursors. Reproduction and profiling here use Chromium 154 on Linux with headless SwiftShader. They do **not** establish Brave-on-Mac hardware performance. No certificate bypass, browser privacy-setting change or TFIS modification is part of this fix.

## Diagnosis and development measurements

The baseline explicitly disabled hardware cursors, causing OpenRA to draw a cursor in the canvas while CSS retained the browser cursor. Input was pumped after rendering, adding another frame before its effects could appear. The extracted browser loop also processed only one logic opportunity per RAF, so a slow software GPU slowed simulation despite cheap managed logic.

A 20-second warm-world CPU/GL sample identified synchronous GPU queries. `getError` dominated CPU samples; after it was batched, `isTexture` became the dominant synchronous call. Removing those texture queries then moved the wait to the final error query. Merely reducing query counts did not solve the main-thread stall.

| Development sample | Simulation ticks/sec | Mean main-thread step | Evidence |
|---|---:|---:|---|
| Accepted baseline | 4.65 | 218.93 ms | 17,766 `getError` calls / 20 s, 18.75 s inside those calls |
| Error queries batched | 5.16 | 201.85 ms | 100 error queries; `isTexture` dominated CPU samples |
| Texture queries removed, final error query retained | 4.77 | 156.35 ms | 16.45 s inside 96 end-of-frame error queries |
| Nonblocking completed-frame validation | 7.64 | 4.16 ms | Managed logic ~1 ms/tick; callbacks still limited by GPU delivery |
| Bounded fixed-timestep catch-up | 24.32 | 5.71 ms | Existing 25-tick rate; ~0.99 ms logic/tick, ~3.83 ms render submission/frame |

These are local A/B development samples, not benchmark claims for a final hosted commit. Raw samples and CPU profiles are in ignored `.runtime/latency-profiles/`. The final exact-head CI supplies the source identity and regression evidence.

The stricter real-input regression measured **24.85 ticks/sec**, **161.05 ms median / 208.50 ms p95** click-to-submission and **410.90 ms p95** click-to-GPU-completed-frame latency. Mouse JS/.NET calls took 2.7 ms total over 77 calls (0.5 ms maximum); the observed managed allocation increase in the idle profiling interval was approximately 0.54 MB/sec. Allocations and interop did not dominate the recorded stall. The software GPU still completes roughly 4–5 game frames/sec: smooth hardware rendering and low actual Mac latency remain to be verified.

The timer refinement subsequently measured **25.04 ticks/sec**, **50.30 ms median / 193.30 ms p95** click-to-submission and **397.70 ms p95** to GPU completion. Maximum observed engine queue age dropped from 205.60 ms to 65.80 ms; mouse interop took 2.6 ms / 77 calls (0.4 ms maximum). Before that refinement, the complete natural match and restart/context recovery passed at tick 5,248, averaging 17.62 ticks/sec while local compiler work also ran. This contention exposed RAF-only logic delivery as a remaining limit; final timer-enabled full-match and exact-commit CI results must be considered separately from the short samples.

## Implementation and bounds

- The engine's original BGRA cursor images and hotspots become browser-managed PNG cursors, scoped to the canvas. Returning real cursor handles prevents OpenRA's software duplicate. CSS size/hotspot follow canvas scaling; the ordinary browser cursor remains outside. No pointer lock is introduced.
- DOM input is dispatched before logic/render. Focus tracks the canvas and document; blur, hidden tabs, pointer cancellation and lost capture release held input. Captured drags still end outside the canvas.
- Owned textures track disposal locally, avoiding `isTexture` queries for each bind.
- A WebGL2 fence follows a submitted game frame. `clientWaitSync(..., 0, 0)` polls without a GPU wait; another render is submitted only after completion. Error validation remains enabled after every completed frame, including actual invalid-command and context-loss failures. Shader compile/link checks remain intact.
- While the GPU is busy, a bounded timer wakes input and the same fixed-timestep simulation independently of RAF delivery. It uses the engine’s next-logic deadline and stops in hidden tabs. Each wakeup processes at most six due logic opportunities within the existing 250 ms jank window. There is no faster game timestep, unbounded background catch-up, alternate simulation or stale-frame render queue. Native engine scheduling is preserved in the source patch's nonbrowser path.

This follows the browser guidance on avoiding [blocking WebGL queries](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/WebGL_best_practices) and the documented [zero-timeout sync query](https://developer.mozilla.org/en-US/docs/Web/API/WebGL2RenderingContext/clientWaitSync). The existing rendering pipeline, shaders and original game content are preserved.

## Reproduce

Build with the pinned SDK/workload in `browser/README.md`, then run:

```sh
python3 tools/profile-browser.py --browser-path /path/to/chromium --label current
python3 tools/test-browser-responsiveness.py --browser-path /path/to/chromium
python3 tools/smoke-browser-world.py --browser-path /path/to/chromium --full-gameplay
```

Profiling warms the real world to tick 100, samples 20 seconds, and records CPU stacks, WebGL calls/times, managed logic/render/input phases and allocation totals. It only observes state. `--bundle` can profile another local bundle; use separate labels and record build identity.

The regression uses actual canvas input under the strict CSP. It checks one cursor, original colors, scaled hotspot/disposal, ordinary outside cursor, scaled selection, captured drag/focus recovery, zero steady texture validity queries, bounded error-query count, at least 20 simulation ticks/sec, submission p95 under 250 ms and GPU-completed-frame p95 under 750 ms on SwiftShader. GPU completion is measured separately from command submission; neither is a physical-display latency claim. A deliberately invalid GL command must still fail. The full skirmish's production, harvesting, combat, AI, win/loss, restart and context-loss assertions remain independently required.

Final integration must use the accepted artifact and recheck the served page. Brave-on-Mac hardware/GPU details and a repeated real-user test remain outstanding; do not attribute the problem to Shields or ask users to weaken browser settings without evidence.
