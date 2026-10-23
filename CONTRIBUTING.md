# Contributing

Frontier Collective is a browser-only RTS using a pinned OpenRA engine and original/reusable assets. Shared C# engine and mod code is retained; native applications and packaging are deferred. Preserve GPL notices and record exact asset sources/licenses in `docs/PROVENANCE.md`.

Use the pinned SDK and browser instructions in `browser/README.md`. Run content/rules/sprite checks, strict Debug compilation, the dependency audit, the WebGL compatibility probe, and full mouse-driven browser gameplay acceptance. Keep production, harvesting, combat, AI and win/loss assertions. Report actual browser/device performance separately from functional headless results.

Keep changes on feature branches for review. Never import proprietary retail art, audio, branding, or game archives. Engine patches live in `browser/engine-patches`; generated `.runtime` source is preserved and must not be hand-edited. Do not change infrastructure, credentials, permissions, or unrelated website routes as part of a game change.

The original SDK contribution guidance remains available at its pinned upstream source recorded in `docs/PROVENANCE.md`.
