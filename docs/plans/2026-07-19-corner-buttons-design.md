# Corner-scheme controls — same chrome idle and riding (2026-07-19)

Shipped over four PRs: **#14** (the scheme), **#15** (worded strip, needle, flank
arrows, uncased picker), **#16** (cache bump), **#17** (single progress-bar arrow,
header cleanup, beep timing). This doc describes the FINAL state; the "review
rounds" section at the end records what changed after #14 and why, since several
decisions reversed things #14 introduced.

## Why

The idle screen used to show control clusters that vanished during navigation
("riding: exactly three interactive elements"), with ride controls buried in the
☰ grid. Riding and planning now share ONE button layout — what you learn on the
driveway is exactly what you use at speed — and the layout finally distinguishes
landscape from portrait/square (the two blessed viewports are 1440×720 and
720×720; nothing used to differentiate them).

## The scheme (all orientations, idle = riding)

- **N** (`#orientCtl`) top-left — north / course / compass cycle. Carries a red
  needle (`#orientNeedle`) that counter-rotates with the map bearing, so it always
  points true north (straight up in north-up mode).
- **box** (`#boxBtn`) top-right — frame the whole track.
- **Base row** (`#baseRow`) along the bottom: **☰** (`#menuBtn`) · **−** · **+** ·
  **dot** (`#dotBtn`, centre on me, wears the lock ring).
  - Portrait / square (`body.portrait`, from `loOrient()`): the four butt up
    edge-to-edge, each exactly ¼ of the screen width.
  - Landscape: normal-size buttons; ☰/dot pin to the corners, − / + sit together
    bottom-centre.
  - ☰ stays at full opacity while riding (everything else dims to `--navOp`) — a
    visibility fix that fades is no fix.
- **− / +**: tap = step zoom. **Hold + saves the turn zoom, hold − the riding
  zoom** — auto-zoom flips between the two saved levels. The old min/max preset
  buttons and jump-taps are gone.
- **START** (`#startBtn`) floats above the dot when stopped; stopping is the ☰
  Demo tile (flips to red **Stop ride** mid-ride — two-tap mis-tap protection).
- **FORWARD / REVERSE** (`#revToggle`) sits above ☰ — START's twin, amber when
  reversed, stopped-screen only. Replaces the old `#revBtn` in settings.
- Riding readouts sit **below** their corner buttons: speed under N (left),
  Varg mode digit under box (right). The turn strip insets between the corners
  (`#hud{left:106px; right:106px}`, rounded bottom corners).
- Everything bottom-anchored stacks off **`--chromeB`** (idle bar height +
  progress-strip height, published by `placeProgress()`), so the countdown
  strip growing lifts the whole row.
- Turn mode hides − / + (ADD MARK owns the bottom centre); ☰/dot stay.

## Turn strip — words, no glyph

Direction word over the road name, distance right: **"Right"** (amber) above
**"Arcadia Rd"** (grey), `145 m` on the right. No arrow glyph and no draining
amber fill — the distance number and the countdown bar already carry proximity.
Falls back to the surface word ("dirt") when a cue has no road name; danger /
gate / creek cues show their words in their own colours.

**Tap = toggle**: grows to the full instruction ("Right on to Arcadia Rd") in
large writing, tap again to shrink. The old 4-second auto-collapse is gone.

## Turn arrows — one, in the progress bar

The giant translucent mid-map arrows are **deleted**. A single solid amber arrow
lives inside the progress bar, vertically centred, on the side of the turn —
left arrow at the left end for a left turn, right at the right for a right,
**never both**. 54 px, growing to 64 px while the countdown bar is up.

These same arrows are the **Varg indicator telltales**: they flash (`.blink`)
when a blinker is live, which outranks a solid turn cue. `applyCdArrows()` owns
both roles; `updateBigArrows` and the giant-arrow tuning knobs (fill / opacity /
surround) are gone.

## Audio grammar (unchanged meaning, fixed timing)

**One tone = right · two = left · three = danger** (the boat convention). The
count was always correct; #17 fixed the *timing*, because two identical 460 Hz
tones 200 ms long with only 100 ms between them fused into a single long beep
through a helmet:

- **Left** = two SHORT pips (140 ms approach / 120 ms turn) with **220 ms of
  silence** between — more gap than pip.
- **Right** = one LONGER tone (260 / 220 ms), so duration reinforces count.

If two pips still read as one on the bike, the next lever is pitching the second
left pip differently — a pitch step survives wind noise better than a gap.

## Glove grid

One unified 3×3 — same tiles idle and riding: Demo(↔Stop) · map type · Mute ·
Tracks · ride type · Auto zoom · Mark spot · Track colour · Settings. The
`data-m` ride/idle split, `gStartStop`, `gOrient` and the zoom-preset tiles are
gone. An explicit ☰ close button (`#gloveClose`) sits bottom-left inside the
overlay — the same spot as the ☰ that opened it, so one location toggles both
ways (tapping empty space still closes too).

## The map is the track picker

Nothing is pre-selected at boot or after loading files: every GPX draws in
**uncased route blue** at full strength, and `fitSelected()` frames them all.
Tapping a track line (~24 px radius, floor 20 m) selects it — it gains the
black/white **casing**, which is the selection signal — and tapping the selected
line again deselects back to the all-tracks view. Non-selected tracks dim only
slightly (0.65) since the casing already arbitrates. Map-tap selection is
stopped-screen only; share-link pack ingest still auto-selects the pack default.

## Track colour (dash patterns retired)

The route is one solid cased line; casing stays auto dark-on-day / white-on-night.
`S.set.trackColour`: **none** (route blue) / **slope** (interior brightness by
grade off the smoothed profile; disabled without elevation) / **surface**
(sealed blue · dirt amber · singletrack purple — replaces the dash patterns and
the `surf` toggle). Interior colour is baked per feature (`c`), with a dimmed
travelled variant (`cd`) so slope/surface still read behind you. Per-surface
layer triplets collapsed to per-state layers (`surf-core/-case/-done/-done-case/
-miss/-recent`).

## Progress strip

Centre label shows **distance to the next cue** (`→ 240 m` / `→ 18.1 km`, from
`ns.cdD`), hidden while off-track so it can't lie. The strip is windowed to the
map, so at rider zoom the next turn is usually off its right edge — this is the
number that matters. Done/remaining labels flank it as before.

## Settings

Full-screen panel closed by a **← back arrow top-left** (`#panelClose`) — no
hamburgers on the settings screen. `showAdv` gates the Stark, Keys and **UI**
tabs together; UI (renamed from Adv) holds the ui rows, the screen-layout editor,
a new **Swap main number** toggle, and the tuning knobs. `ctlEdges` ("Control
buttons on") and `gloveSide` are removed.

## Demo pacing — highlight reel

The plain demo no longer plays flat 10×. It sprints each gap at a **constant
per-gap velocity** so the next audible cue is ~3 s away (capped just under
`progContM` so travelled spans stay continuous), drops to ride pace 250 m out so
the auto-zoom dive, countdown and beeps play in real time (~3 s), carries 40 m
past the turn, then sprints again. Cue-less tracks fast-forward at the cap.
Training keeps its real-time 1 Hz pacing.

> Implementation note: the sprint velocity is computed **once per gap**, not per
> tick. A per-tick `(gap - APPR_M) / TICKS` fraction decays asymptotically and
> never arrives — that bug shipped in the first draft and was caught by sampling
> position every second.

## Migration (`_v5`)

Deletes `surf`/`ctlEdges`/`gloveSide` and the dash adv knobs, seeds
`trackColour:'none'`, prunes removed ids from saved layouts and remaps a saved
`followBtn` slot to `dotBtn`.

> The dead-key deletes run **unconditionally**, not inside the `_v5` flag check:
> a cache-first SW means an old app version can re-seed those keys from its own
> defaults after the flag is already stamped.

## Demo (training ride)

Training cards re-targeted: box lesson (`ev:'fit'`), dot lesson, − / +
hold-to-save lesson (`trainEvent('preset')` moved into `presetSet`), new N-cycle
card, glove copy lists the new tiles. `#trainCard` anchors off `--chromeB`.
Position words in the copy track the #15 swap (box "top right", ☰ "bottom left").

## Review rounds — what changed after #14, and why

| # | Change | Reason |
|---|---|---|
| 15 | ☰ and box swapped (☰ into the base row bottom-left) | ☰ is the most-used control; the base row is the thumb zone |
| 15 | Settings closes via ← top-left, not a hamburger | Two hamburgers on one screen read as two menus |
| 15 | On-map FORWARD/REVERSE toggle | Reversing a ride was buried in settings |
| 15 | Compass needle on the N button | Mode glyph alone didn't say which way north was |
| 15 | Tracks uncased until selected; others dim only 0.65 | Dimming hid tracks you were trying to choose between |
| 15 | Turn strip → words, no arrow glyph | The glyph crowded the strip on a phone |
| 17 | Giant map arrows deleted; progress-bar arrow takes both roles | The translucent arrow covered the map it was drawn over |
| 17 | One arrow on the matching side, not both flanks | Two arrows don't say "left" |
| 17 | Header fill bar deleted | Redundant with the distance number and countdown bar |
| 17 | Beep pips shortened, gap widened | Two same-pitch tones 100 ms apart fuse under a helmet |

## Verification status

Verified in the preview browser at 1440×720 and 720×720 only. Everything
physical — beep timing through a helmet, gloved taps on the ¼-width base row,
the 600 ms hold-to-save, arrow glanceability in peripheral vision, the compass
needle under real magnetometer jitter — is **still unvalidated on the bike**.
