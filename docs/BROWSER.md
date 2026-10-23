# Browser port — current status

**The actual Frontier world now runs locally in Chromium; full browser acceptance and deployment are pending.** No remote desktop or replacement engine is being built. The working desktop baseline remains at `main` commit `70a1ff084e9ff5557bab26c17f1588cd678293ae` until real browser acceptance passes. Then remove desktop entrypoints, packaging, workflows, dependencies and documentation that the browser no longer needs, preserving shared engine code and recoverable Git history. Native desktop/mobile apps are deferred until demand warrants them.

## Architecture and cost

Run OpenRA's simulation, Pioneer AI, rendering and input on the player's device through .NET WebAssembly and WebGL2. Serve versioned files through Cloudflare Workers Static Assets. The current engine already has an in-memory `EchoConnection` for local orders; adapting skirmish/session setup to use it avoids a gameplay server for single-player.

[Cloudflare documents free, unlimited static-asset requests and no additional asset-storage cost](https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/). Its [platform limits](https://developers.cloudflare.com/workers/platform/limits/) cap individual static files at 25 MiB. Keep static requests on the asset-serving path; do not invoke a Worker for every file. No Containers or always-running compute are needed for this design. Optional account/save APIs and later multiplayer signaling/relay would be separately metered functions. A relay is not authoritative simulation; multiplayer design is deferred.

The environment's earlier read-only Cloudflare token/account API requests failed at its network proxy with HTTP 403. They were not retried or bypassed. Token validity and account permissions remain unverified. No infrastructure, credentials, tunnels or security permissions were created. Local browser development does not require that API access.

## Tested milestone

The browser feature branch now boots the actual Salt Basin map, OpenRA world renderer and HUD in WebGL2, using the original assets and fonts. A real local session starts the human and Pioneer AI through the existing in-memory order connection. Browser events have selected and moved a scout and constructed/placed the generator, refinery and fabricator; both players have delivered salvage. Combat-unit production and full combat/win-loss acceptance remain under test.

The earlier isolated compatibility probe remains a separate check of inherited rules, reflection, PNG decoding, full RGBA GPU readback and scaled pointer input. It starts no world. See [world/probe instructions, measurements, source review and remaining gates](../browser/README.md). Desktop gameplay evidence does not satisfy the browser gates. Nothing has been deployed to Cloudflare.
