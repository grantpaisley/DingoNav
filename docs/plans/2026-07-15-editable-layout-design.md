# Editable screen layout (edit mode) — design

**Date:** 2026-07-15 · **Status:** approved, implementing

Picks up the parked "drag-to-rearrange control layout" entry in
`future-developments.md`. **Purpose note:** this is primarily a *design tool for
Grant* to find the right UI layout on the tablet — it may never be surfaced to
end users. That means: prioritise function over polish, no glove-ergonomics
constraints inside edit mode itself (normal riding UI is untouched).

## Decisions (from brainstorm, 2026-07-15)

- **Scope:** buttons + big readouts. Editable set = the floating chrome:
  orient / follow / fit / sound, zoom −/+ and the two zoom presets, START fab,
  ☰ menu button; readouts: speed (`#hudSpeed`), Varg battery pill
  (`#vargPill`), Varg mode digit (`#vargModeBig`), indicator telltales
  (`#vargInd`). The **turn strip stays fixed** — safety-critical, its top-band
  layout is load-bearing. Bottom bar, panels, pills (`hold`/`lock`) untouched.
- **Custom overrides adaptive:** an element with a saved slot is positioned
  absolutely (inline styles) and no longer participates in the adaptive
  shuffling (`body.navving …` offsets). Elements *without* a saved slot keep
  stylesheet defaults, including adaptive rules. The turn-strip zone is shown
  as a reserved band in edit mode and the grid starts below it.
- **Resize = tap to cycle S/M/L** on readouts while editing (multipliers
  0.7 / 1 / 1.4 via a CSS var; buttons don't resize).
- **Entry:** "Edit screen layout" button in ☰ → Settings → General. Exit via a
  floating ✓ Done pill. Edit mode is unreachable while navigating (☰ opens the
  glove overlay then), so it never coexists with the riding hot path.
- **Wobble** while editing (single CSS keyframe, per-element phase offset) as
  the "taps are disarmed" indicator. Dropped if it ever fights the drag code.

## Data model

```js
S.set.layout = {
  portrait:  { followBtn: { slot: '0-2' }, hudSpeed: { slot: '2-0', size: 'L' }, muteish… },
  landscape: { … }
}
```

- Orientation = `innerWidth > innerHeight ? 'landscape' : 'portrait'`
  (aspect-ratio, **not** `screen.orientation` — split-screen lies).
- Slot id `"<col>-<row>"` on a **5 col × 6 row** grid, or `"panel"` (docked).
- Absent key = stylesheet default. Empty orientation = fully default (adaptive
  rules live). One `saveSet()` per drop, nothing on the hot path.

## Slot grid

- Columns: 5 anchors — left edge (+10px), 25%, 50%, 75%, right edge (−10px).
  Edge columns anchor the element's edge (`left:10px` / `right:10px`), middle
  columns centre it (`left:X%; translateX(-50%)`).
- Rows: 6 equal cells between a **top reserve** (~64px, turn-strip zone) and a
  **bottom reserve** (~64px, menu/progress strip + dock tray). Element is
  vertically centred in its cell (`translateY(-50%)`).
- Geometry computed from the live viewport at apply-time — no stored pixels;
  rotation and split-screen just re-run `applyLayout()`.

## Edit-mode interactions

- Enter: close panel, `body.editing`, materialise every editable element to a
  fixed pixel rect (its current position), show grid dots + reserved band +
  dock tray + ✓ Done / ↺ Reset pills, bind pointer handlers. All clicks on
  editable elements are suppressed by a capture-phase listener.
- Drag: pointer capture, live `left/top`; nearest slot dot highlights.
- **Displacement:** hovering an occupied slot pushes the occupant to the next
  free slot **below** in its column, else the next free **to the right** in its
  row, else left, else anywhere free — recomputed per hovered slot from the
  committed state so dragging away reverts automatically. Commit on drop.
- **Dock tray:** slim full-width bar at the very bottom while editing
  ("drop here to dock into ☰ menu"). Buttons only (not readouts, not ☰
  itself). Docked → `slot:'panel'`; in normal use docked buttons render as a
  strip at the top of the ☰ panel, still tappable. Drag out of the tray to
  re-place on the grid. One home per element by construction.
- Tap a readout while editing → cycle S/M/L.
- Reset (per current orientation): wipe `layout[orient]`, back to defaults.
- Exit: unbind handlers, clear edit chrome, `applyLayout()`, final `saveSet()`.

## Rendering

- `applyLayout()` runs at boot, on viewport change (resize listener + the
  existing 1s watchdog), and on edit exit. Per entry: docked → reparent into
  `#dockStrip`; slotted → inline `position:fixed` + computed left/right/top.
  Freed buttons stay children of their `.ctlgroup` (inline `fixed` removes
  them from the flex flow; group CSS sizing still applies).
- Readout size: `data-sz` attr + `--sz` var; CSS `calc()` rules scoped to
  `[data-sz]` so untouched elements keep default (incl. media-query) sizing.
- Ghosts: `body.editing` forces conditional elements visible at ~55% opacity.
- Hot-path safety: identical argument to the parked spec — nothing per-fix or
  per-frame touches any of this; drag machinery bound only while editing.

## Known limits (accepted for v1)

- Only slotted elements occupy grid cells; a default-positioned element can
  visually overlap a dropped one (move it too, or reset).
- No undo beyond Reset; no cross-orientation copy.
- `env(safe-area-inset-*)` isn't readable from JS; reserves use constants
  generous enough for the tablet.

## Test checklist

Drag/snap/displace by hand; rotate round-trip (portrait edits don't leak to
landscape); split-screen resize recomputes slots; dock round-trip (dock mute →
tap it in ☰ → drag back out); ghosted conditionals land where placed; reload
applies layout with no default-position flash; Reset restores defaults and
adaptive rules; SW cache bumped.
