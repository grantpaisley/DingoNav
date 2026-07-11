# Ride-feedback design — 2026-07-11

Design from field feedback (road + MTB singletrack ride, phone at half screen).
Core complaint: **way too many beeps**. Core insight: a beep should mean
*"the obvious move here is wrong"* — warn when the route leaves the way you'd
naturally continue on.

Build order: §1 cue engine → §2 zoom → §3 riding screen → §4 cue editing → §5 map styles.

---

## 1. Cue engine — beep only when the obvious move is wrong

Drop the two noisy triggers:

- **Geometry fallback** (`TURN_LONE` beep on sharp bends over unmapped ground) — gone.
  This is most of the singletrack noise: twisty trail ≠ decisions.
- **Standalone heatmap-junction cues** — gone as their own beep type. The heatmap grid
  remains *evidence* for the decision test below.

A cue now fires only where **all three** hold *(revised after the round-1 field test:
hairpin cues and straight-ahead cues are gone — see below)*:

1. **Way transition** — the smoothed way-class/name under the track changes
   (road→track, named→named, track→path, mapped→unmapped).
2. **The departed way continues** — sampling the basemap grid around the transition,
   the way you were on (matched by name, else class) carries on somewhere the route
   doesn't. Keeps shire-boundary renames and flow-through trail joins silent
   (no decision = no beep).
3. **It's an actual turn** — peak bearing change ≥ `TURN_MIN` around the transition.
   Going straight ahead needs no warning, even onto another way.

Revisions from the round-1 field test (2026-07-11, built as cue4):

- **No hairpin cues** — you can see a hairpin on the map, and recorded
  obstacle-retry loops (riding circles to get up/around an obstacle) fake them.
- **No straight-ahead cues** — superseded the original "straight onto a minor way
  while the main road bends off" case; only real turns cue.
- **No way data at all** within ~40 m → silent (don't guess). A genuinely unmapped
  route past a *mapped* alternative is still caught: test 2 keys off the alternative.
- **Look-through** — a way-match dropout (<300 m, same way both sides) is not a
  departure + rejoin.

**Turn-confirmation chirp**: after passing a cue and staying on-track ~40 m /
a few seconds, play the existing back-on-track chirp once. Settings toggle
"Turn confirmation", default **on** — answers "did I take the right fork?".
Off-track buzz logic unchanged.

**Per-mode tuning**: thresholds and lead times live per vehicle mode
(walk/mtb/enduro/adv), so enduro and ADV converge on their own numbers.

Bump the cue-cache version so all tracks re-analyse under the new rules.

## 2. Zoom — vehicle presets, heart favourite, manual hold, centre lock

Speed→screen-span curves per vehicle preset (span = metres of visible map height;
numbers are starting points, tune in demo mode + rides):

| Preset | stopped | mid | fast |
|---|---|---|---|
| Walk   | 150 m | 250 m @ 5 km/h  | 400 m @ 8 km/h    |
| MTB    | 250 m | 500 m @ 15 km/h | 900 m @ 35 km/h   |
| Enduro | 300 m | 900 m @ 30 km/h | 2.5 km @ 70 km/h  |
| ADV    | 400 m | 2 km @ 50 km/h  | 7 km @ 100 km/h   |

One "vehicle" setting drives beep lead-times, zoom curve, per-mode cue tuning, and
per-mode heart zoom. Walk gets a lead-time row too (short leads, low speeds).

- **Manual hold**: any manual zoom (pinch / ± / controller) while auto-zoom is on
  switches to *hold* — zoom stays put, ignoring speed. When the next cue's
  far-warning window approaches (~15 s out), auto-zoom re-engages smoothly.
  "⤢ held" pill shown while holding; tap to release early.
- **Heart favourite**: after a ± nudge, a heart fades in next to the buttons.
  Tap → current zoom saved as the favourite (per vehicle mode; heart fills).
  Favourite replaces the speed curve as cruise zoom: auto-zoom still pulls in to
  frame each turn, then returns to heart zoom. Tap filled heart to clear → back
  to pure speed curve. No heart = plain hold behaviour above.
- **Centre lock**: long-press on the map toggles a lock. Locked = pinned centred,
  pans/drags ignored (glove-brush protection at speed). Long-press unlocks for free
  browsing; while unlocked + panned away, long-press snaps back to centre and
  re-locks in one gesture. Small padlock indicator shows state.
- **Controller (DMD2 etc.)**: pairs as Bluetooth HID keyboard → listen for `keydown`.
  Defaults: `+`/`-`, arrow up/down, media next/prev = zoom. Settings row captures
  any keycode ("press your controller button…"). Mappable actions: zoom in/out,
  mute, re-centre, north/course toggle, map style flip.

## 3. Riding screen — marker, HUD, controls, fullscreen

- **Arrow marker**: replace the dot with a navigation dart/chevron rotated to the
  smoothed course bearing (held when stopped, as course-up does now). Accuracy halo
  stays underneath.
- **Turn HUD**: replace the centre-screen arrow overlay with one slim semi-transparent
  top strip: turn arrow + "onto <way name>" left, live distance right, strip fill
  drains left→right toward the turn point. Course-up: arrow shows turn direction;
  north-up: arrow rotates to the turn's actual bearing.
- **On-screen controls** (~35% opacity until touched): `+`/`−` stacked on the
  glove-side edge (respects glove-side setting), heart under the ± pair, mute toggle
  in the top corner (slash icon when muted, one tap, no menu). Fit / re-centre /
  glove overlay stay as-is.
- **Fullscreen**: menu ⛶ entry via the Fullscreen API; auto-request on START,
  release on STOP. iOS Safari lacks the API → show "Add to Home Screen for
  fullscreen" hint there. Installed PWA already standalone.
- **North-up discoverability**: make the existing N-button state more obvious
  (it already toggles north-up/course-up but wasn't found on the ride).

## 4. Planning — editable turns

Select a track (not navigating) → "✎ Cues" button next to START enters edit mode:
cue dots grow tappable, route highlights.

- **Remove**: tap a cue dot → greys out (soft-delete; never beeps, hidden from HUD).
  Tap again to restore.
- **Add**: tap the route line → cue created at nearest track point; direction/angle
  and "onto" name computed from local geometry + way grid. Long-press a dot to cycle
  turn → hairpin → delete.
- **Done** exits; toast "n cues (m edited)".

**Persistence**: edits stored as an *overlay* (removals + additions keyed by
distance-along-track) separate from the analyser cache. Re-analysis re-runs the
algorithm then re-applies the overlay, so hand edits survive algorithm upgrades.
Overlay lives in IndexedDB and travels with exported/shared bundles (group rides
share curated cues).

**Tuning loop**: hand-deleted cues are the classifier's false positives. Menu →
copy diagnostics exports overlays for tightening per-mode thresholds against
real rides.

## 5. Map styles + route surface rendering

Three presets = one base `layers.json` + small colour/width override tables
(not forked files). Same pmtiles, instant switch, no extra storage. Picker in
settings (thumbnail swatches); mappable to a controller button for day/night flips.

1. **Dark** — current look, for night.
2. **Daylight** *(new default)* — light warm ground, dark road casings, green forest
   tint, strong water. Readable in full sun.
3. **High-contrast trail** — pale ground, loud track/path colours (tracks orange,
   paths magenta-dashed), beefed-up widths.

Overlay colours (heatmap, selected track, position arrow) get per-style variants —
the neon-on-dark palette disappears on light ground.

**Route surface styling**: the route line encodes surface from the cue analyser's
way-class array (`m.cls` — already sampled under the whole route, no new data):

- solid = sealed (road classes)
- long dashes = dirt / fire trail (track class)
- short dots = singletrack (path class)
- unmapped stretches = dashed (dirt is the safe guess)

A continuous faint casing renders underneath the patterned line so the route never
visually breaks against busy terrain; the pattern reads as texture on top.

## Settings after all this (⊕ new)

vehicle mode walk ⊕ /mtb/enduro/adv (drives beep lead-times, zoom curve, per-mode cue
tuning, per-mode heart zoom) · sound on/off · ⊕turn confirmation chirp ·
auto-zoom on/off · ⊕map style picker · ⊕controller key mapping · glove side ·
orientation north/course · group ride name/code.
