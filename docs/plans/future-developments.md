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

## Drag-to-rearrange control layout (editable button placement)

**Update (2026-07-15): picked up and implemented.** Design brainstormed and built —
see `2026-07-15-editable-layout-design.md`. Scope grew beyond this sketch: wobble
edit mode, 5×6 slot grid with launcher-style displacement, readout S/M/L sizing,
separate portrait/landscape layouts, dock tray → ☰ panel strip. Note the reframe:
it shipped as a **design tool for Grant** (reachable via Settings → General), not
a rider-facing feature — the glove-ergonomics caveats below apply to *using* the
resulting layout, not to edit mode itself. Original parked entry kept below for
the reasoning.

**Decision (2026-07-14): parked as a possible enhancement, not scheduled.** Phase 1
of the control-layout rework shipped (split left/right groups, floating START, slim
hamburger, free-ride, and a **Left-right / Top-bottom** edges option in Settings →
General). This entry is "Phase 2": let the rider *drag* individual buttons around the
screen or dock them into the hamburger menu panel, Android-launcher style, with the
layout persisted. Held back so the fixed/preset layout could be lived with first —
if the shipped edge options already feel right on the bike, this may never be needed.

Sketch specs if picked up:

- **Explicit Edit mode, never ambient.** A dedicated Edit button (e.g. in the ☰ panel,
  or a long-press on the hamburger) toggles editing. Outside Edit mode buttons behave
  exactly as now — a plain tap fires instantly. Do **not** make buttons
  press-and-hold-to-drag during riding: that adds tap-vs-drag latency, which fights the
  gloved, glance-and-go priority.
- **Each button lives on-screen or in the menu panel.** Dragging a button down onto the
  hamburger opens the panel; keep dragging to drop it inside (docked = hidden from the
  map, reachable via ☰). Dragging one out of the panel places it back on the map.
- **Persistence:** store per-button placement (edge/offset or x/y as a fraction of the
  viewport so it survives rotation and split-screen) in `S.set`, saved via `saveSet()`.
  One write on drop; nothing during riding.
- **Reset to default:** a one-tap "Reset layout" so a mis-drag is trivially undone.

**Performance note (why it's safe):** the hot path (per-GPS-fix, per-map-frame) is
untouched. Positions are applied once from saved state on load via CSS/transform and
never recomputed while navigating. The pointer-drag machinery is bound only while Edit
mode is active — dormant otherwise. Hand-rolled pointer events, no library, a few KB in
the single-file app. If the rider never opens Edit mode it's as if the feature isn't there.

**Also skipped in the same round (2026-07-14): a landscape/portrait lock button.**
Requested as "clicking toggles landscape/portrait, default landscape." Dropped for now
because a web app can't force device rotation on iOS at all (Apple blocks
`screen.orientation.lock`), and on Android it only works for an installed PWA in
fullscreen — so a true lock is Android-only and unreliable. The CSS-rotate-the-whole-UI
alternative is a hack that fights the split-screen support added earlier. Revisit only
if the app is wrapped natively, or if an Android-only best-effort lock is judged worth it.
