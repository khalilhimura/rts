# Roadmap

1. Complete exact-head browser-only CI and deploy the verified artifact at `thefutureissolo.com/rts/` through authorized TFIS infrastructure, preserving unrelated routes.
2. Profile real browser/GPU performance. The initial headless software run is functionally complete but slow. Measure rendering, interop, memory and simulation timing before runtime/AOT work or any Rust decision.
3. Improve the single-map skirmish: balance costs/ranges, add difficulty and clearer power/production/victory feedback, expand browser lifecycle/accessibility coverage, and test fog/shroud together with visibility rules.
4. Polish original terrain/buildings/UI and CC0 unit animation; add original audio and accessible cursor variants. Keep exact source/license records.
5. Add maps, infantry, defenses, a second faction and technology upgrades; design multiplayer command ordering/desync tests separately. A relay is not authoritative simulation.

The active product is browser-only. Native applications are deferred until demand warrants them. Shared browser-required engine code and recoverable history remain; desktop packaging is removed. The current prototype has one orthogonal map, mirror factions, finite salvage, simple AI and silent combat. Lua campaigns, naval/air units and an isometric terrain conversion are outside this milestone.
