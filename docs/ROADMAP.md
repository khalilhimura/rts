# Roadmap

1. **Browser-native first:** complete the [browser port gates](../browser/README.md): actual world/HUD boot, local simulation and Pioneer AI, then browser input/production/harvesting/combat/win-loss acceptance. Use client-side simulation and static asset delivery; retain source pins, licenses and the advisory gate. Profile before any [Rust decision](RUST-ASSESSMENT.md).
2. **Switch the active product to browser-only:** after gameplay acceptance, remove desktop entrypoints, packaging/workflows and dependencies the browser does not need, preserving shared engine code and recoverable Git history. Desktop/mobile native apps wait for demand. Do not expand native packaging tests now.
3. **Improve the skirmish:** tune costs, ranges and AI attack timing; provide difficulty options; add attack-move/stop buttons and clearer production, power and victory feedback. Expand automated browser gameplay coverage. Add fog/shroud rendering together with visibility tests.
4. **Replace temporary presentation:** polish original terrain/buildings/UI; integrate CC0 firing, motion and destruction animations; add original audio and accessible cursor variants. Check visual facing order and terrain transitions.
5. **Expand carefully:** additional maps, infantry, defensive structures, a second original faction, technology upgrades, then multiplayer desync and balance tests. Keep source pins and provenance current.

The current milestone has one orthogonal map, mirror-faction skirmish, finite salvage, a simple AI and silent combat. Campaigns, naval/air units, superweapons, an isometric terrain conversion and public distribution are outside this first milestone.
