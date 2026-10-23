# Browser port — current status

**Browser-native single-player is the chosen direction. It is not playable or deployed yet.** No remote desktop or replacement engine is being built. The working desktop baseline remains at `main` commit `70a1ff084e9ff5557bab26c17f1588cd678293ae` until real browser acceptance passes. Then remove desktop entrypoints, packaging, workflows, dependencies and documentation that the browser no longer needs, preserving shared engine code and recoverable Git history. Native desktop/mobile apps are deferred until demand warrants them.

## Architecture and cost

Run OpenRA's simulation, Pioneer AI, rendering and input on the player's device through .NET WebAssembly and WebGL2. Serve versioned files through Cloudflare Workers Static Assets. The current engine already has an in-memory `EchoConnection` for local orders; adapting skirmish/session setup to use it avoids a gameplay server for single-player.

[Cloudflare documents free, unlimited static-asset requests and no additional asset-storage cost](https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/). Its [platform limits](https://developers.cloudflare.com/workers/platform/limits/) cap individual static files at 25 MiB. Keep static requests on the asset-serving path; do not invoke a Worker for every file. No Containers or always-running compute are needed for this design. Optional account/save APIs and later multiplayer signaling/relay would be separately metered functions. A relay is not authoritative simulation; multiplayer design is deferred.

The environment's earlier read-only Cloudflare token/account API requests failed at its network proxy with HTTP 403. They were not retried or bypassed. Token validity and account permissions remain unverified. No infrastructure, credentials, tunnels or security permissions were created. Local browser development does not require that API access.

## Tested milestone

The separate browser feature branch adds a **compatibility probe**, not a game. It executes the actual pinned OpenRA/Common/Frontier managed assemblies in Chromium's WebAssembly runtime, resolves inherited Frontier actor rules, loads a production trait through OpenRA reflection, decodes the CC0 eight-direction scout sheet with OpenRA, verifies every uploaded RGBA pixel through WebGL2 readback, and tests scaled pointer input through the real engine input interface.

See [probe instructions, measurements, source review and remaining gates](../browser/README.md). No `World` or AI is started by the probe. Selection, movement, building placement, production, harvesting, combat and win/loss remain unverified in browser. Desktop gameplay evidence does not satisfy those browser gates.
