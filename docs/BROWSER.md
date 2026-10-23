# Browser architecture and delivery

Frontier Collective now executes the actual OpenRA simulation, Pioneer AI, renderer and input on the player's device through .NET WebAssembly and WebGL2. The first complete browser match passed all gameplay gates through decisive win/loss; desktop-only product files were then removed. Final exact-head browser-only validation is in progress. Nothing is deployed yet.

The pinned engine source is acquired from `browser/engine-source.json`; tracked patches/additions produce a separate hash-addressed build tree. Existing EchoConnection carries single-player orders without a TCP game server. Browser FontFace/Canvas rasterizes the exact GNU FreeSans files. Rules use the existing synchronous loading path; static maps require no filesystem watcher; unsupported GC compaction is skipped. The browser menu restarts through a fresh browser session.

## Hosting and cost

The authorized target is **https://thefutureissolo.com/rts/**. Serve the verified static bundle under that prefix and preserve all unrelated TFIS routes. See [integration requirements](TFIS-DEPLOYMENT.md). Single-player simulation needs no Worker execution, Containers, always-running server or remote desktop.

[Cloudflare documents free unlimited static-asset requests and no additional asset-storage cost](https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/), with a [25 MiB per-file limit](https://developers.cloudflare.com/workers/platform/limits/). Keep file requests on the asset-serving path. Optional save APIs or future multiplayer relays would be separately metered; a relay is not authoritative simulation. Those functions are deferred.

The current environment's earlier token/account API requests were blocked by its network proxy with HTTP 403. Access and token permissions remain unverified. No credentials, tunnels, paid infrastructure or security permissions were created, and that denial was not retried or bypassed. Deployment requires an authorized TFIS delivery environment or restored permitted access.

## Remaining product work

The first software-rendered browser match advanced roughly 3 ticks/second against a configured 25; this is a material performance limitation. Measure real GPU browsers, memory and frame/tick timing, then profile rendering/interop and evaluate runtime/AOT options. Do not infer performance from the primitive interop probe. No Rust rewrite has been approved; see [assessment](RUST-ASSESSMENT.md).

Native desktop/mobile apps, multiplayer and Lua campaigns are deferred. Source history preserves the previous baseline. See [browser setup and tests](../browser/README.md), [validation](VALIDATION.md), and [roadmap](ROADMAP.md).
