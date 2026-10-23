# Validation record — 2026-10-23

## Environment and baseline

Work ran in the selected `rts` cloud environment at `/workspace/rts`. Before editing, `git remote -v` identified `https://github.com/khalilhimura/rts.git`; the checkout had no commits or files. No `AGENTS.md`, run instructions or `.agents/skills` were present in the checkout or workspace instruction directory. Work is isolated on `feat/first-playable-skirmish`.

Debian 13 x86_64; local .NET SDK 8.0.426 and runtime 6.0.36 installed under `/workspace/toolchain/dotnet`. No system installation, credentials or permission expansion was performed. Native desktop testing used the environment's existing Xorg dummy driver at `:99`, SDL2, Mesa llvmpipe / OpenGL 4.5, 1280×800. This was an actual OpenRA desktop client with real mouse input, not a browser recreation or a headless-only simulation. There is no audio output device; audio playback has not been verified and the prototype's notification pools are silent.

## CI repair follow-up

Hosted run [39904828668](https://github.com/khalilhimura/rts/actions/runs/39904828668) on the first delivered commit failed its explicit Debug style build with 14 upstream IDE diagnostics. Release/content checks passed. The runner had installed SDKs 6/8 but selected preinstalled SDK 10.0.401; the initial repository lacked `global.json`.

The follow-up pins SDK **8.0.426** with roll-forward disabled and asserts it in CI. Root `Directory.Build.targets` updates the effective `NuGet.CommandLine` reference to the advisory's patched **6.12.5** without editing the verified engine archive. CI now runs unmodified strict `make check` with **no** NU1901 exception. `tools/check-dependencies.py` fails on reported direct or transitive vulnerabilities, validates the actual resolved patched client, and rejects incomplete/error reports; regression tests exercise vulnerable transitive and unpatched cases. All seven content tests, full rules/Fluent checks, sprite decoding, strict `make check` and the transitive audit passed locally after this fix. The package audit checks the three projects loaded by Frontier (mod, Common and Game), including their transitive NuGet dependencies. The strict Debug build reports zero warnings and errors.

The engine still targets retired .NET 6, producing NETSDK1138 warnings in its Release executable projects; this is disclosed and not hidden or waived. Package audit success is not a claim of a supported runtime or production security review. A supported-runtime engine migration remains on the roadmap.

`tools/smoke-desktop.py` adds real XTest mouse-driven desktop gameplay validation (no injected state) for selection/movement, all buildings, production, both economies and a decisive combat result. It passed locally after the dependency fix through tick **4928**, with real destruction leading to human `Lost` / AI `Won`; see `docs/evidence/ci-repair-smoke.log`. Hosted CI runs it under an isolated virtual X display and uploads its evidence. Hosted CI status for the final exact feature/main commits must be verified from their runs, rather than inferred from local results.

Hosted run [39930294262](https://github.com/khalilhimura/rts/actions/runs/39930294262) confirmed the pinned SDK, build, strict style, content and dependency checks passed, but exposed unreliable fixed wall-clock waits in the new desktop driver. The driver now waits for the real production queue's ready state, reported by read-only diagnostics once per 25 simulation ticks. Software rendering uses two Mesa worker threads, disables VSync and caps rendering to the game frame rate; simulation rules and game speed are unchanged. Failures retain a screenshot and print the last observed state for diagnosis.

Browser delivery is assessed separately in [BROWSER.md](BROWSER.md): no browser deployment has been made.

## Original milestone checks (historical, before CI repair)

| Check | Result |
|---|---|
| `make` (engine + mod Release build) | Passed; upstream runtime/advisory warnings remain |
| Fresh engine acquisition into a separate temporary directory | Passed SHA-256 and preserved full upstream lint source |
| `python3 tools/test-content.py` | 5 passed: source hashes, PNG sheets/chrome geometry, map routes/salvage reachability, existing-work preservation, checksum-failure handling |
| `TREAT_WARNINGS_AS_ERRORS=true ./utility.sh --check-yaml` | Passed mod, default sequences, full Fluent references and both maps; no lint warnings |
| `./utility.sh --check-frontier-sprites` | Passed actual decoding of every referenced sequence frame and exact four-vehicle build roster, excluding preview actors |
| `./utility.sh --check-explicit-interfaces` | Passed |
| `./utility.sh --check-conditional-trait-interface-overrides` | Passed |
| Debug build with all style diagnostics as errors, retaining NU1901 as a visible warning | Passed: `dotnet build Frontier.sln -c Debug --no-restore -warnaserror -warnnotaserror:NU1901` |
| Stock SDK `make check` | **Fails** because `-warnaserror` promotes upstream NU1901 to an error; not claimed green |
| Generated content reproduced from checked-in sources | Byte-for-byte check recorded in evidence |
| Windows/macOS builds, installer packaging, network multiplayer/desync, save/load, editor | Not validated |

Before the follow-up override, the pinned engine referenced `NuGet.CommandLine 6.12.1`, for which NuGet reports [GHSA-g4vj-cjjj-v7hg](https://github.com/advisories/GHSA-g4vj-cjjj-v7hg). It also targets the retired .NET 6 runtime. These are upstream baseline limitations, not suppressed globally. The original CI retained the advisory as a warning. The follow-up above removes that exception and resolves the advisory; upgrade the retired runtime before a distributable release.

## Desktop outcomes

- Direct `play.sh` starts one human and Pioneer AI on Salt Basin, with distinct player colors and command hubs plus patrols.
- Actual mouse clicks queued and placed generator, refinery and fabricator; the HUD unlocked the expected build options. Preview actors are excluded from production.
- Selecting and right-clicking moved a scout. Selection health bars and control-group hooks render; rally-point production exits work.
- Both players' crawlers harvested real resource cells, docked, and credited their owners. A human delivery of 20 bales produced 800 credits; the screenshot shows partial unload credit ticks.
- The human fabricator produced tank, artillery and scout actors. AI built its own structures, delivered resources, produced combat vehicles, routed through the central rock lanes, and attacked.
- Projectiles, health loss, unit kills and structure destruction were observed in the running client. A completed match ended with human `Lost` / AI `Won` after destruction of the human buildings. The final review run also exercised the fixed camera and complete production roster, and ended at tick **4959** with human `Lost` / AI `Won`. The human earned **6400** harvested credits and recorded **4** kills.

`docs/evidence/skirmish.png` shows the latest review client with all four structures, produced units, harvesting credit ticks and incoming enemies. `docs/evidence/combat.png` records an earlier desktop firefight. Diagnostic snapshots and concise check output are retained beside them. Diagnostics read the world without injecting units, credits, damage, or production orders.

## Repeat the smoke test

After building:

```sh
FRONTIER_DIAGNOSTICS=1 ./play.sh 2>&1 | tee .runtime/smoke.log
```

1. Confirm the camera starts at your hub; select a scout and move it with a right click.
2. Build/place generator, refinery, fabricator. Confirm cash expenditure, prerequisites and the refinery's free crawler.
3. Watch at least one full delivery. Build a tank, artillery and scout. Select the fabricator and set its rally point.
4. Fight the AI: verify projectiles, damage, kills and loss of structures. Continue until one side's structures are destroyed; check victory/defeat and return/restart behavior.
5. Run `python3 tools/check-runtime-log.py .runtime/smoke.log --require-victory`. The checker requires both economies, the human roster and new tank actor, human scout movement, combat kills and a decisive outcome. Omitting `--require-victory` permits an in-progress combat smoke check. It validates recorded evidence; it does not automate mouse input.

On a cloud runner without a display, build/rules/sprite/content checks remain available but do not prove interactive gameplay. The Xorg configuration used here is saved in `docs/evidence/xorg-dummy.conf`; it uses the existing dummy video driver and software OpenGL. Cloud .NET cache paths need to point inside writable workspace directories; no project code depends on those absolute paths.

## Review/publishing

The repository remote had no branch refs before this work. The original implementation and evidence were committed and successfully pushed using the environment's Git connection to [feat/first-playable-skirmish](https://github.com/khalilhimura/rts/tree/feat/first-playable-skirmish). GitHub CLI separately reported its `GH_TOKEN` invalid, but that did not prevent the Git push. No credentials were generated. There is no separate existing base branch against which to open a draft PR, so no PR was created. At that original milestone no base branch, merge, installer release or public deployment was created. Subsequent user authorization permits safe initial `main` creation after the repaired feature commit is green; preserve its existing history.
