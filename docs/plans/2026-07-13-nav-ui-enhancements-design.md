# Nav UI enhancements — design

Validated 2026-07-13. Covers the nine-item enhancement batch for the riding/navigation UI.

## 1. Zoom control stack

Right-edge column, top to bottom: `+` `−` `min` `med` `max` `▢` `●`.

- `+` / `−` — unchanged (manual zoom = hold until next turn approach).
- `▢` — fit whole track (existing fitBtn, relocated).
- `●` — re-centre on location (existing, relocated).
- `min` / `med` / `max` — zoom presets stored per vehicle in `S.set.zoomPresets[vehicle]`.
  - **Tap** — fly to that level and hold (same semantics as manual zoom-hold; released at next turn approach).
  - **Hold ~600 ms** — capture the current zoom as that preset. Toast "min zoom set — L12.4"; button label changes from placeholder word to `L12`.
  - Internal per-vehicle defaults (min = turn-approach zoom, max = cruise zoom, med = midpoint) so auto-zoom works before anything is user-set; labels stay `min`/`med`/`max` until user-set.

**Auto-zoom simplification.** The speed curve and the ♥ favourite zoom are removed. Cruise rides at `max`; turn approach dives to `min`; `med` is a manual bookmark only. Setting renamed "Auto-zoom". Existing ♥ favourites migrate into `max` on first load.

## 2. Compass mode

- **Trigger** — new setting "Compass when zoomed in": *at turns* (default) / *above zoom threshold* / *off*. *At turns*: when `ns.approach` goes true, orientation temporarily switches to compass; reverts to the prior mode (north/course) when the approach ends. *Threshold*: driven by crossing a zoom level (advanced knob). Manual N-button cycling overrides the automatic flip until the next approach.
- **Damping** — EMA factor 0.25 → ~0.12 (advanced slider); dead-band ignoring heading changes < ~2°; map rotation rate-limited to ~4 Hz with eased rotation; damping doubles when stationary.

## 3. Route rendering

Two independent channels: **colour = steepness, pattern = road surface.** Settings toggles "Steepness colouring" (default on) and "Road-surface patterns" (default on):

| Steepness | Surface | Render |
|---|---|---|
| on | on (default) | grade-coloured line, dashed/dotted by surface |
| on | off | grade-coloured solid line |
| off | on | single track-colour, dashed/dotted by surface |
| off | off | plain solid single-colour line |

- Tracks without elevation fall back to surface/plain automatically (existing arbitration).
- Quick toggles beside the selected track in the ☰ panel for mid-ride flipping.
- **No outside lines**: the dark `sel-casing` layer is deleted. Non-steepness modes get a same-colour translucent halo (~30 % opacity, wider, dash pattern matched to each segment). Steepness mode draws the bare gradient with no outline. Dash/dot gaps are fully transparent — no brown underlay.
- Combined mode implementation: intersect grade bands (already stepped) × surface runs into features carrying colour + surface; the three surface layers paint `line-color: ['get','c']`.

## 4. Heatmap / basemap colours (advanced)

Colour pickers: own rides (`#ff7a00`), other riders (`#ff2d2d`), planned (`#3390ff`), and the basemap minor-trail override (`#e06d00` — the orange clash). Plus a "basemap trail prominence" slider (width/brightness of the override).

## 5. Bottom bar & START/STOP

START/STOP and ⇄ reverse move into the ☰ panel as a prominent top row (big START + reverse toggle beside the selected track). Bottom bar keeps only ☰ + track name. STOP remains a glove tile. The freed strip hosts the countdown bar.

## 6. Countdown bar

Bottom strip has two modes:

- **Cruising** — current viewport-matched progress strip, unchanged.
- **Turn approach** (`ns.approach`, the same signal driving compass flip and min-zoom dive) — fixed full-width bar filling left→right as `dTo` shrinks from the activation distance to zero. Large label counts down in **metres or seconds** (settings choice; seconds = `dTo ÷ speed`, frozen when stopped). Bar colour: accent, then warn-amber inside the near distance. Snaps back to progress strip once the turn is confirmed. Activation distance is an advanced knob.

## 7. Backtrack trail (breadcrumbs)

While navigating, record the actual ridden path — a point every ~20 m (advanced knob) — in `S.trail`, persisted to IndexedDB every minute (survives restart mid-ride). Rendered as a muted dotted line under the route. Settings toggle on/off. Trail auto-clears when navigation of a *different* track starts; kept after stopping for post-ride review. Keeps recording off-track, providing a visible thread back to the route.

## 8. Buttons transparent while routing

All floating controls (zoom stack, N, glove button, hold pill) drop to a low opacity while `body.navving`, returning to full opacity on touch and fading back after a few seconds. Opacity level is an advanced knob.

## 9. Settings tabs

Settings panel reorganised into tabs: **General** (name, ride code, screen-on, glove side, map style, Strava overlay) · **Nav** (sounds, vehicle, auto-zoom, compass-when-zoomed-in, countdown units, route colouring, backtrack trail) · **Keys** (hardware key bindings) · **Advanced** (hidden behind a "Show advanced" toggle in General).

## 10. Advanced tab (dev-tuning console)

Every row: slider/stepper with current value, live effect, per-row reset. Persisted in `S.set.adv{}`. A "Copy tuning" button dumps the JSON so tuned values can be hardcoded later and rows graduated out.

- **Compass & camera** — heading damping EMA; heading dead-band (°); camera ease durations (900 ms follow / 500 ms orient).
- **Alerts & cues** — per-vehicle far/near alert distances (`VEH` table); turn-approach framing multiplier (`farM × 1.5`, floor 250 m); off-track leave/return (`OFF_M 60` / `ON_M 40`); beep volume.
- **Zoom & countdown** — default min/med/max per vehicle; countdown activation distance; metres↔seconds.
- **Rendering & misc** — routing button opacity; trail dot spacing/retention; route halo opacity & width; heatmap/basemap colours (§4); GPS accuracy floor.

## Phase 2 (separate design): POIs & track grading

Imported GPX files often carry `<wpt>` waypoints and per-track grading/colours (e.g. multi-track files like G.O.A.T.). `parseGPX` currently drops waypoints entirely. Phase 2 covers: waypoint parsing + storage, POI map layer with names, per-track colour/grading extensions, and multi-track file handling. Deliberately excluded from this batch to keep it reviewable.
