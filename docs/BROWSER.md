# Browser delivery assessment — 2026-10-23

**Status: not deployed; no playable browser URL exists for this repository.** The desktop prototype remains intact. No ports, tunnels, Access policies, credentials, subscriptions or paid services were created.

## Native browser execution

The pinned OpenRA SDK builds a desktop .NET/SDL2/OpenGL program. Uploading its native binaries to Cloudflare Pages/Workers is not a browser export. Workers' server-side Wasm support does not provide a desktop renderer or convert this client into a WebGL application.

[Rosebud's April 2026 engineering report](https://rosebud.ai/engineering/porting-openra-to-the-browser) demonstrates that an actual OpenRA Wasm port is possible. It describes renderer/input/filesystem changes, a managed Lua compatibility layer and replacement browser networking. Its linked play page points back to the standard OpenRA/SDK repositories; a separately reusable source tree, license inventory and reproducible build recipe for those browser changes were not located in this assessment. The linked retail-content demo is not a deployment of Frontier Collective and its game assets were not downloaded or reused.

That report is a promising research lead, not a ready export target for this checkout. Integrating a source-verified port would be a significant separate engine/platform change. Before authorizing that route, obtain its modified GPL source and build instructions, verify compatibility with this mod DLL and original assets, and budget a separate browser validation pass. Static Cloudflare hosting becomes appropriate only after a genuine browser bundle exists and gameplay has been verified there.

## Preserve the native game through browser streaming

The smaller technical route is remote-desktop streaming: the actual native OpenRA process runs on a Linux host with a display and software/GPU OpenGL. Browser input and frames are transported through [Cloudflare's authenticated browser VNC support](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/use-cases/vnc-browser-rendering/) or an isolated noVNC/Selkies service behind an existing authenticated access layer. This is **remote execution**, not browser-native simulation. Rendering latency, concurrent sessions, keyboard handling and session cleanup need testing.

The user reports an existing Workers Paid subscription; this is not authorization for new container usage. No existing persistent Linux game host, public hostname or Cloudflare Access application/policy was identified in the repository or selected environment. Read-only requests to `https://api.cloudflare.com/client/v4/user/tokens/verify` and `/accounts` failed at the environment's network proxy with `Tunnel connection failed: 403 Forbidden`. That proves this environment cannot currently perform those calls; it does not establish whether the supplied token itself is valid or which account permissions it has. No access expansion or repeated credential attempts were performed.

The Codex development display is ephemeral test infrastructure, not an authorized persistent public game host. A static screenshot or landing page would not satisfy browser play.

## Concrete choices requiring user input

| Route | Compute/cost requirement | Access requirement | Work remaining |
|---|---|---|---|
| Existing Linux host + existing Cloudflare Access app | Potentially no **new** recurring cost if suitable compute and service are already paid/owned; account availability is unverified | Identify the host and existing application/hostname, authorized user policy and permitted deployment mechanism; keep VNC bound privately | Build an isolated game session, connect through the existing authenticated path, test actual gameplay in browser |
| New Cloudflare Containers host | Existing Workers Paid subscription satisfies the base-plan requirement; new container usage and overages are not approved. [Published pricing](https://developers.cloudflare.com/containers/platform/pricing/): 25 GiB-hours/month memory and 375 vCPU-minutes/month included, then $0.009/GiB-hour and $0.072/vCPU-hour, plus disk/egress and Workers/Durable Object usage. Containers have no Free allowance. Actual account usage/headroom is unverified | Explicit billing approval and permission to configure the host/Access/tunnel path; currently blocked API access must be resolved by the user | Measure suitable instance size and latency, quote expected usage, provision only after approval, then validate authenticated browser play |
| Reusable native Wasm port | A source-verified export might use static hosting; porting effort and compatibility are presently unverified | Explicit approval for the larger engine/platform integration, and access to corresponding port source/build recipe | Integrate original mod content, compile/export, validate browser input/production/combat/endgame and all notices |

There is no validated no-new-cost public browser deployment path available with the currently identified infrastructure and access. The next decision is whether to supply an existing host/Access app or authorize a separately scoped port/hosting setup. CI and publication to `main` can be completed independently.
