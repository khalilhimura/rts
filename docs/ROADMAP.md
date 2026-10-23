# Roadmap

1. **Harden the baseline:** move to an OpenRA release/toolchain with a supported .NET runtime; resolve the pinned `NuGet.CommandLine` advisory. Test Windows/macOS startup and clean-machine dependency installation before distributing installers.
2. **Improve the skirmish:** tune costs, ranges and AI attack timing; provide difficulty options; add attack-move/stop buttons and clearer production, power and victory feedback. Automate desktop input smoke coverage. Add fog/shroud rendering together with visibility tests.
3. **Replace temporary presentation:** polish original terrain/buildings/UI; integrate CC0 firing, motion and destruction animations; add original audio and accessible cursor variants. Check visual facing order and terrain transitions.
4. **Expand carefully:** additional maps, infantry, defensive structures, a second original faction, technology upgrades, then multiplayer desync and balance tests. Keep source pins and provenance current.

The current milestone has one orthogonal map, mirror-faction skirmish, finite salvage, a simple AI and silent combat. Campaigns, naval/air units, superweapons, an isometric terrain conversion and public distribution are outside this first milestone.
