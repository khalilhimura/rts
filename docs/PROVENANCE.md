# Sources and license evidence

Verified 2026-10-23. This repository is a modified OpenRA SDK project, not an EA game-content port. Active content mounts only `mods/frontier`, engine root assemblies, and `engine/mods/common`; it does not mount the engine's classic-game mods or content installers. No retail sprites, sounds, logos, disk images, MIX files, SHP files, or game archives were imported.

## Engine and SDK

| Component | Source pin | License / retained evidence |
|---|---|---|
| OpenRA Mod SDK | [20250330](https://github.com/OpenRA/OpenRAModSDK/tree/0059e22e0e3bfc862500aaaa9fe1aed4ea4e994a), commit `0059e22e0e3bfc862500aaaa9fe1aed4ea4e994a` | GPLv3; `COPYING`, original file headers, `docs/SDK-README.upstream.md` |
| OpenRA engine | [release-20250330](https://github.com/OpenRA/OpenRA/tree/524b6abdf1874b0132a7b06c1f89c7012f60124c), commit `524b6abdf1874b0132a7b06c1f89c7012f60124c` | GPL-3.0-or-later per source headers; fetched source retains `COPYING`, `AUTHORS`, dependency notices; `licenses/OpenRA-AUTHORS.txt` preserves a copy |
| SDK UI | SDK `mods/example/chrome/assets/dialog.png`, `glyphs.png`; cursor `default.png`; editor markers `mapeditor.png`, `mpspawn.png` and corresponding YAML | Retained from the above GPL SDK baseline; original chrome definitions adapted. The example logo was replaced by an original mark. |
| SDK packaging artwork | Same pinned SDK, `packaging/artwork/*.png` | Retained unchanged under the SDK baseline license; placeholder installer icons/backgrounds are not used by the desktop prototype; packaging remains unvalidated |
| Common UI and fonts | Pinned engine `mods/common`, including GNU FreeFont `FreeSans.ttf` / `FreeSansBold.ttf` | GPL according to engine `AUTHORS`; fetched with source, not duplicated or relicensed as CC0 |
| Browser platform, DOM input and GLSL | [openra-wasm `wasm` branch](https://github.com/Baronvonbonbon/openra-wasm/tree/424fb8b08d98de057015bc2cfcaddeaf10f3cc14), commit `424fb8b08d98de057015bc2cfcaddeaf10f3cc14` | GPL-3.0-or-later; original hashes/adaptations in `browser/platform-imports.json`, preserved headers and `browser/licenses/`; no fork mods or retail archives imported |

Engine archive: `https://github.com/OpenRA/OpenRA/archive/524b6abdf1874b0132a7b06c1f89c7012f60124c.zip`

SHA-256: `401b46b32ebddd04ea5ad342528195afe555d0800a7bbb5e07d00f3eb5b9e2ec`

`mod.config` and `tools/fetch-engine.py` pin and verify this archive before extraction. A source receipt is stored inside ignored `engine/`. Existing directories with a different/missing receipt are preserved. Unlike the stock SDK acquisition script, this project's script keeps `CheckFluentReferences.cs`; full localization lint is enabled. No engine gameplay source changes are required. The follow-up root `Directory.Build.targets` overrides the effective `NuGet.CommandLine` package from upstream 6.12.1 to patched 6.12.5 for GHSA-g4vj-cjjj-v7hg; the engine archive stays intact. `global.json` pins SDK 8.0.426. The stable engine's source includes unused classic-game mod definitions, but this project does not install their retail content.

## PixVoxel models

Author: **Tommy Ettinger / TEttinger**. Credit retained voluntarily.

The recommended [OpenGameArt eight-direction pack](https://opengameart.org/content/pixvoxel-colorful-isometric-wargame-sprites) lists **CC0** and describes the models and artwork as made by the author. The archive URL `https://opengameart.org/sites/default/files/PixVoxel_Wargame_2.7z` returned HTTP 403 in this environment, so none of that archive was imported. Instead, the linked [author's source repository](https://github.com/tommyettinger/PixVoxelAssets) supplied these four models at commit **`99dd229ab1cb39101fc0dda554883fc0dfe1be8b`**. Its root LICENSE is CC0 1.0 Universal, and its README explicitly includes voxel models under CC0. Copies of both are in `licenses/`. No bundled third-party executables, renderers or libraries from that repository were imported.

Each source path is `PixVoxelAssets/PixVoxelAssets/CU2/<filename>` at that exact commit:

| Model | Used for | SHA-256 |
|---|---|---|
| `Tank_S_Large_W.vox` | Skipper Scout | `e583d149319bd4937cbb58cc29d685e1f0ffe0dc5e81c71a4402a328d48c7284` |
| `Tank_Large_W.vox` | Bulwark Tank | `e9d47822efcb1a5a3b65e835a5ac71e1aa94ec8ccc6adab7549382625568ed69` |
| `Artillery_S_Large_W.vox` | Pike Artillery | `9262cc7306d722aeaf72b797a7b57fe68072d664c77d4ff490205cbab9f4989c` |
| `Truck_Large_W.vox` | Salvage Crawler | `33f3af3e78f6a33fe15d1954510690e05a7aef316a7d81780f235c99a61d42c7` |

The source models and machine-readable manifest are checked into `assets/sources/pixvoxel/`. `tools/generate-content.py` contains a new small renderer, palette mapping, projection and eight rotations. Rendered outputs are derived CC0 artwork. The original pack's pre-rendered animation frames were not copied; there is currently one still frame per facing.

## Original content

Four building sprites, salt terrain, rocks, roads, salvage crystals, placement overlays, production clock, icons, tiny bitmap lettering, faction mark, map layout, faction names and game rules were created for this prototype on 2026-10-23. Reproducible generators are in `tools/generate-content.py`; no image-generation service or proprietary asset tools were used. New art/data images are dedicated to CC0 in `licenses/ORIGINAL-ASSETS.txt`; generator and runtime code and YAML rules use GPL-3.0-or-later. Sound notification definitions are intentionally silent. There is no music or imported audio.

Changes to SDK source include the mod/project rename, skirmish loader, camera initialization, diagnostics, validation command, build acquisition and CI. Preserve notices when redistributing; the different art license does not change the engine/code license. Packaging is deferred and no installers or public release have been produced.
