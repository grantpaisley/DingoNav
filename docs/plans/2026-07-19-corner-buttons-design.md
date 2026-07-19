# Corner-scheme controls — same chrome idle and riding (2026-07-19)

## Why

The idle screen used to show control clusters that vanished during navigation
("riding: exactly three interactive elements"), with ride controls buried in the
☰ grid. Riding and planning now share ONE button layout — what you learn on the
driveway is exactly what you use at speed — and the layout finally distinguishes
landscape from portrait/square (the two blessed viewports are 1440×720 and
720×720; nothing used to differentiate them).

## The scheme (all orientations, idle = riding)

- **N** (`#orientCtl`) top-left — north / course / compass cycle.
- **☰** (`#menuBtn`) top-right — glove grid; also where the full-screen settings
  close from (`#panelClose` sits in the same spot).
- **Base row** (`#baseRow`) along the bottom: **box** (`#boxBtn`, whole track) ·
  **−** · **+** · **dot** (`#dotBtn`, centre on me, wears the lock ring).
  - Portrait / square (`body.portrait`, from `loOrient()`): the four butt up
    edge-to-edge, each exactly ¼ of the screen width.
  - Landscape: normal-size buttons; box/dot pin to the corners, − / + sit
    together bottom-centre.
- **− / +**: tap = step zoom. **Hold + saves the turn zoom, hold − the riding
  zoom** — auto-zoom flips between the two saved levels. The old min/max preset
  buttons and jump-taps are gone.
- **START** (`#startBtn`) floats above the dot when stopped; stopping is the ☰
  Demo tile (flips to red **Stop ride** mid-ride — two-tap mis-tap protection).
- Riding readouts sit **below** their corner buttons: speed under N (left),
  Varg mode digit under ☰ (right). The turn strip insets between the corners
  (`#hud{left:106px; right:106px}`, rounded bottom corners).
- Everything bottom-anchored stacks off **`--chromeB`** (idle bar height +
  progress-strip height, published by `placeProgress()`), so the countdown
  strip growing lifts the whole row.
- Turn mode hides − / + (ADD MARK owns the bottom centre); box/dot stay.

## Glove grid

One unified 3×3 — same tiles idle and riding: Demo(↔Stop) · map type · Mute ·
Tracks · ride type · Auto zoom · Mark spot · Track colour · Settings. The
`data-m` ride/idle split, `gStartStop`, `gOrient` and the zoom-preset tiles are
gone.

## Track colour (dash patterns retired)

The route is one solid cased line; casing stays auto dark-on-day / white-on-night.
`S.set.trackColour`: **none** (route blue) / **slope** (interior brightness by
grade off the smoothed profile; disabled without elevation) / **surface**
(sealed blue · dirt amber · singletrack purple — replaces the dash patterns and
the `surf` toggle). Interior colour is baked per feature (`c`), with a dimmed
travelled variant (`cd`) so slope/surface still read behind you. Per-surface
layer triplets collapsed to per-state layers (`surf-core/-case/-done/-done-case/
-miss/-recent`).

## Settings

Full-screen panel, hamburger top-right closes it. `showAdv` gates the Stark,
Keys and **UI** tabs together; UI (renamed from Adv) holds the ui rows, the
screen-layout editor, a new **Swap main number** toggle, and the tuning knobs.
`ctlEdges` ("Control buttons on") and `gloveSide` are removed.

## Migration (`_v5`)

Deletes `surf`/`ctlEdges`/`gloveSide` and the dash adv knobs, seeds
`trackColour:'none'`, prunes removed ids from saved layouts and remaps a saved
`followBtn` slot to `dotBtn`.

## Demo

Training cards re-targeted: box lesson (`ev:'fit'`), dot lesson, − / +
hold-to-save lesson (`trainEvent('preset')` moved into `presetSet`), new N-cycle
card, glove copy lists the new tiles. `#trainCard` anchors off `--chromeB`.
