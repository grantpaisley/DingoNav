# Possible future developments

A running backlog of ideas that are **not** committed to the roadmap — parked here
so the reasoning survives after any exploratory branches are deleted. Nothing here
is scheduled; each entry records the decision and enough spec to pick it up later.

## 3D view (tilted/perspective map)

**Decision (2026-07-13): out of the DingoNav navigation product.** A tilted 3D
camera does not serve turn-by-turn riding — the nav UI is deliberately flat,
north-up (or heading-up) 2D so cues, the route line and the countdown strip stay
legible at a glance on the bars. Terrain is already conveyed by the offline
hillshade relief under the trails (see `make_hillshade.py`), which gives ridge/gully
readability without tilting the camera.

**Possible home: Dingo, later — as a "show off a track" flourish, not navigation.**
A one-off cinematic/preview mode for reviewing or sharing a completed track, clearly
separate from the riding view.

Sketch specs if picked up:

- **Where:** Dingo (the desktop/library app), not DingoNav. A "preview" / "flyover"
  action on a selected track, never engaged while navigating.
- **Camera:** MapLibre pitch (~45–60°) + bearing, with the DEM already loaded as a
  `raster-dem` source driving real `terrain` exaggeration (the hillshade extract is
  terrarium-encoded, so the same tiles feed `map.setTerrain({ source: 'dem' })`).
- **Motion:** optional auto-flyover that follows the track polyline start→finish
  (animate camera along the line), or free tilt/orbit for a static showcase.
- **Scope guard:** display/marketing only — no cue rendering, no live GPS, no
  auto-zoom. Keep it out of the nav code paths so it can't regress the riding UI.

**Status of the exploratory branch:** `claude/3d-view-navigation-aolaq8` never
contained any 3D work — its HEAD was the already-merged hillshade commit. Deleted
2026-07-13; nothing lost.
