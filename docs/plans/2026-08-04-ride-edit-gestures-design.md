# Ride & edit gesture redesign — tap-to-add, point menu, double-tap zoom

2026-08-04. Replaces TURN MODE, centre lock, and the heatmap knockout with a
flat gesture model shared by riding and cue-edit mode.

## Gesture model

Riding (`S.nav`) and edit mode (`S.cueEdit`) share one table:

| Gesture      | On a point        | On the track                  | Empty map |
|--------------|-------------------|-------------------------------|-----------|
| Tap          | Open point menu   | Add a turn point immediately  | —         |
| Double-tap   | Zoom toggle       | Zoom toggle                   | Zoom toggle |
| Long-press   | —                 | Track picker (stopped only)   | —         |
| Drag / pinch | Pan / zoom — always live, no centre lock |         |

- Tap hit-tests points first (~30 px radius), then the track (25 m). A hit on
  a point — including one placed a second ago — opens the menu. A hit on bare
  track places a `turn` mark, direction inferred from geometry
  (`inferTurnDir`), snapped to the nearest track vertex, saved through the
  existing `addTurnPointAt` → overlay → pack-sync path. No arming step, no
  picker on the way in.
- Riding places against any analysed track; edit mode restricts both
  hit-tests to the selected track.
- Stopped and *not* in edit mode, taps only select/deselect tracks
  (`trackTap`) — placement is gated behind riding or edit mode.
- The 280 ms tap/double-tap disambiguation window applies everywhere now
  (planning included), so a tap can't collide with the zoom gesture.

## Double-tap zoom toggle

- While riding, double-tap eases to the "zoom in" preset
  (`max(16.5, zoomForSpan(presetSpan('min')))`), compass-up to the course
  bearing, rider low-third (18% offset), stashing the prior zoom. The next
  double-tap eases straight back to the stashed zoom (and bearing 0 if
  orientation is north-up). This inherits what was good about TURN MODE and
  drops the rest.
- Strictly manual both ways — no auto-return when riding past the junction.
- Exempt from the speed gesture-lock: double-tap works at any speed. Pinch
  and rotate stay guarded.
- Stopped/planning keeps MapLibre's normal incremental double-click zoom.

## Point menu (mark picker regrown)

Full-screen picker, fixed 12-slot grid: 2 rows × 6 columns landscape,
4 rows × 3 columns portrait (CSS grid switched on `body.portrait`).

- Slots 1–9: the nine kinds from `MARKS`, Turn keeps its direction chip
  (auto → L → R → S).
- Slot 10: **Delete** — red tile, only live when the picker opened on an
  existing point. One tap, no confirm (the point is one tap from re-added).
  In edit mode, deleting a base cue keeps the restore semantics
  (`ov.removed`); greyed removed dots open the menu with **Restore** in the
  red slot instead.
- Slots 11–12: blank, reserved for two future POI kinds — rendered as faint
  empty cells so the grid never reflows when they arrive.

Placing a non-turn POI is two taps, no modes: tap the track (turn point
appears) → tap the point → pick the kind.

## Removals

- **Centre lock** — `setLock`, `S.lock`, `#lockPill`, the `dotBtn.locked`
  ring, lock branches of the long-press handler, its train events and coach
  references. `dragPan` is never disabled.
- **TURN MODE** — `enterTurnMode`/`exitTurnMode`, `S.turn`, `setMarkArm`,
  `#markTurn`, `#turnHint`, all `body.turnmode` CSS, the arming/removed/move
  branches of `rideTap`. Its camera behaviour lives on in the double-tap
  zoom toggle.
- **Heatmap knockout** — `maskedHeatData`, `heatMaskCache`, the `heatU`
  source and `heat-under` layer, the `heatMask`/`heatUnderOp` settings and
  sliders. The heatmap renders whole under the route.
- **Long-press** shrinks to one job: stopped only, near a track → track
  picker.

## Recentre dot & base row

- The dot shows only when the map is away from the rider
  (`S.follow === false` — set by drag, the box/fit button, or anything that
  pans off). While following it fades to invisible (~200 ms,
  `pointer-events:none`); its slot in the row is held so ☰ / − / + never
  move. `recentreTap` unchanged; the `active` lit-dot styling goes.
- Base row: four equal cells in both orientations (landscape drops the
  clustered auto-margin layout). Riding: tiles get larger (~104 px) and
  near-transparent (icon + faint outline, full opacity on `:active`),
  keeping the `--navOp` idle fade. Stopped keeps the solid look.

## Touchpoints

`index.html` throughout; coach/tour steps that taught double-tap-for-turn-mode
and the lock; `docs/settings-reference.md` loses `heatMask`/`heatUnderOp`.
