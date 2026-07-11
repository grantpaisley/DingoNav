# DingoNav v2 — Orientation, Progress, Turn Cues

*Designed 2026-07-11 with Grant. Guiding priorities: simplicity and speed. Default
screen stays "a dot and a heatmap."*

## Scope

Four additions to the existing MapLibre+PMTiles nav app:

1. Orientation modes: north-up / course-up (no compass mode in v1)
2. Progress strip: distance/time done vs to go, turn ticks, optional elevation profile
3. Import-time route analysis: turn-cue extraction using basemap road/track classes,
   steepness coloring
4. Ride-time turn alerts: speed-tuned timing, glance card, vehicle presets

Explicitly cut for v1 (keep it simple):

- **Curve warnings** — turns only. A turn is a *decision point*; a curve is just
  geometry. The analysis data (heading changes, severity) is retained at import, so
  curve heads-ups can be added later behind a setting without re-architecting.
- **Compass-up mode** — phone magnetometers near a running bike are off by 20–40°
  (ignition, alternator, bar-mount steel) and need a calibration UX. The frozen
  approach bearing in course-up covers the stopped-at-a-junction case.
- **Rerouting** — this is a follow-the-line app. Off track = buzz; ride back.
- **Progress-strip interaction** beyond expand/collapse (no scrubbing, no
  tap-a-tick) — that is planning behavior, this is a riding screen.
- **Speed coloring on import** — steepness only. Speed ramps are unreadable at nav
  zoom in sunlight, compete with heatmap colors, and plans have no timestamps anyway.

## Responsive requirement (added 2026-07-11)

The layout must work in **portrait, landscape, and half-screen** (split-screen /
half of a bar-mounted display). Short viewports (≤500 px tall) compact the HUD,
hide the bottom bar while navigating (STOP lives in the glove overlay), pin the
progress strip to the screen edge, and reflow the glove grid (one row of six when
wide, 3×2 otherwise). A 1 s watchdog re-places the chrome on viewport changes that
never fire a resize event (split-screen drags).

## 1. Main screen & orientation

Default screen: basemap, heatmap, route line, position dot, progress strip along the
bottom, one fat button (~68 px) in the bottom corner on the throttle-free side
(setting: left/right). Nothing else.

**Orientation** — compass rose in a fixed corner; tap toggles north-up ⇄ course-up.

- Course bearing comes only from GPS fixes above ~7 km/h, low-pass smoothed.
- Below that threshold the map holds the **last valid approach bearing** — stop at a
  junction and the map keeps pointing the way you arrived.
- The rose always shows where north is.

**Glove button** — opens an overlay of ~6 tiles, each ≥ 80 px: orientation, zoom
lock/auto, mute, profile strip on/off, steepness coloring on/off, end nav. One stab
each; overlay auto-dismisses after ~8 s or on map tap. Everything else (vehicle
preset, friends, bundle management, warning tuning) lives in a settings screen used
while stopped.

**Auto-zoom** — existing speed-driven easeTo stays; the zoom-lock tile freezes it.

## 2. Progress strip

One component along the bottom edge, two states, toggled by tap or the glove tile.

**Collapsed (default)** — thin bar (~14 px): fill = distance covered; **turn cues as
ticks**; end labels `12.4 km · 0:58` done / `10.7 km · ~0:52` to go.

- ETA-remaining uses the **rolling moving average** speed (same window as warning
  lead), ignores stopped time — a snack stop doesn't inflate it.

**Expanded (profile)** — strip grows to ~70 px; fill becomes the elevation profile
(area sketch from `<ele>`, LTTB-decimated once at import). Position dot rides the
profile; ticks along the top edge. With steepness coloring on, the profile fill uses
the steepness ramp.

**Semantics**

- Position on the strip is **route-distance** from the existing
  follow-from-nearest-point projection — out-and-backs and switchbacks behave.
- Off-track: strip dims, labels freeze (no fake ETA); resumes on rejoin.
- Everything pre-computed at import; ride-time work is "move a dot along an array."

## 3. Import-time route analysis (cue engine)

One-shot analysis when a route is imported or selected for nav (progress spinner,
seconds not minutes). Decision from brainstorm: **on-device, at import** — works
with any GPX from anywhere, no Dingo round-trip, zero per-frame cost. It must read
track/road class from the basemap, not just heatmap geometry.

**1. Corridor decode** — compute the route's z14 tile cover, fetch those tiles from
the local PMTiles blob (IDB), decode only the `roads`/`paths` layers plus loaded
heatmap tracks into line features with OSM class: `track` (fire trail), `path`
(singletrack), minor/major road, etc.

**2. Way matching** — walk the route, match each stretch to the underlying way
(nearest feature within ~15 m, compatible bearing). Output: segment list
("0–4.2 km on *track*, 4.2–6.8 km on *path*…"), also used for the glance card's
"onto singletrack" text.

**3. Cue classification** — at each point where route heading changes ≥ ~25° over a
short window, *or* the matched way changes:

- **TURN** ⇔ an alternative continues where you don't go: the way you were on
  carries straight past the departure point, or another mapped/heatmap way leaves
  the junction. Angle may be shallow — a way-class change alone qualifies (the
  fire-trail→singletrack case, easy to miss at 30°).
- No alternative ⇒ no cue (curves cut from v1; severity data still recorded).
- Cues within ~30 m merge into one (junction clusters).
- Unmatched stretches (unmapped trail, nothing in basemap or heatmap): fall back to
  geometry-only — turns require a much larger angle since alternatives are invisible.

**4. Steepness + profile** — per-point grade from `<ele>` (smoothed ~75 m window,
same approach as Dingo's web profile), plus the LTTB-decimated profile.

Results cached in IDB keyed by route+bundle hash — re-opening re-imports nothing.

## 4. Ride-time turn alerts

The nav loop walks the baked cue list; no analysis while riding.

**Timing: time-based, distance-clamped.** Far warning ~15 s ahead, near ~5 s, from
rolling moving-average speed. The **vehicle preset** (enduro / MTB / adventure) sets
min distances (e.g. 40/15 m MTB, 120/40 m adventure) so crawling doesn't warn too
late, and a max so fast fire-trail running doesn't warn 500 m early. The preset also
drives auto-zoom aggressiveness.

**Sound** — three sounds in the whole app: turn-far (double beep), turn-near (higher
triple), off-track (buzz). Existing WebAudio implementation. Mute tile silences all.

**Glance card** — on the far warning, a large card slides in above the progress
strip: arrow from turn geometry, live countdown distance, onto-line when known —
**"↰ 150 m · onto singletrack."** Stays through the turn; flips green briefly once
position matches the post-turn route direction; dismisses. Blown turn: card goes
red, off-track buzz takes over.

**Missed-cue guard** — cues are consumed by route-distance, not proximity: passing
route point *n* marks all earlier cues stale, so a GPS jump can't fire ghost
warnings behind you.

## Implementation notes

- Tile decode needs a vector-tile parser over the pmtiles JS lib (both vendorable;
  no CDN, consistent with the offline rule).
- A 50 km route covers ~100 z14 tiles; decoding one layer per tile is sub-second
  scale — but show the spinner anyway.
- All new ride-time state is array-walking + one DOM card; nothing added to the
  render loop.
