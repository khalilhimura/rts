# TFIS integration: /rts/

Authorized destination: **https://thefutureissolo.com/rts/**. Publish the actual verified game bundle only after full browser acceptance and exact-head CI pass. The current environment cannot publish: earlier Cloudflare token/account requests were blocked by its proxy with HTTP 403; no bypass or credential changes were attempted. Use an already authorized TFIS delivery environment or restore permitted access.

## Artifact and routing

CI produces `rts-site-<source commit>` containing `.runtime/rts-site.zip`. The ZIP contains only the `rts/` subtree, including index, JavaScript/CSS, `_framework/*.wasm`, original content, build identity and licenses. Merge that subtree into the existing site's static output. Do not replace the TFIS site root, global Worker/router configuration, existing assets, redirects, headers or unrelated routes.

- Redirect exact `/rts` to `/rts/` (308), preserving a query if present.
- Serve `/rts/*` as static files from that subtree. Missing game files must return 404, not the TFIS SPA/HTML fallback.
- Preserve relative URLs and filenames. No root-relative game asset URLs or simulation Worker are required.
- Return `.wasm` as `application/wasm`, JavaScript as a JavaScript MIME type, CSS as `text/css`, PNG as `image/png`, JSON as `application/json` and fonts as their normal font MIME type. Never return HTML for a runtime/asset request.
- Revalidate `/rts/` and its files (`Cache-Control: no-cache` is suitable initially). Runtime filenames are not all content-addressed, so do not mark them immutable across releases. Cloudflare may apply normal transfer compression; do not rename files to add compression suffixes.
- Scope any required policy changes to `/rts/*`. The local test uses `default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; worker-src 'self' blob:; object-src 'none'; base-uri 'self'`. It requires no general JavaScript `unsafe-eval`, inline script/style allowance, cross-origin isolation, SharedArrayBuffer, network tunnel or remote desktop. Review existing TFIS policy before integration; do not weaken it globally.

The browser owns single-player simulation and AI. Use the existing static-asset delivery path, with no per-asset Worker invocation, Containers or new paid compute. Do not create credentials, permissions or a second service as a workaround for the current access denial.

## Verification after authorized publication

Check the exact build identity at `/rts/world-build.json` against the green source commit and artifact. Verify the redirect, MIME/cache headers, 404 handling and absence of root-path asset requests. Run real browser acceptance against the published path (selection, movement, build/produce, harvest, combat/AI, win/loss, restart and context recovery). Confirm representative existing TFIS routes still behave as before. A screenshot, probe or static landing page is not playable-deployment evidence.

TFIS currently injects Meta Pixel into HTML during its build. Exclude the standalone `public/rts/**` documents from that injection, or explicitly review and test any route-scoped instrumentation policy before publishing. Do not weaken the game CSP globally or silently add external script/inline allowances. Test the final post-build HTML served by TFIS; the original artifact alone does not verify a modified page.
