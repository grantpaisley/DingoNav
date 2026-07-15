# Ride UI Overhaul — Design

**Date:** 2026-07-15
**Trigger:** First major test ride. Functionality ~80% there; the UI fails on the small
screen. Verdict: the layout concept doesn't survive contact with a small screen — rebuild
it from "what do I need while moving" first.

## Context & constraints

- **Screen today:** 720×720 — DingoNav shares the Varg dash with the stock UI.
- **Screen endgame:** 1440×720 — once DingoNav shows the telemetry the stock UI shows,
  the stock half is redundant and DingoNav takes the full dash.
- **Design for 1440×720 as the true form; 720×720 is a degraded mode we must survive.**
  (Inverts the previous assumption that square is first-class.)
- **Input:** touch-first (gloves, vibration). Bar controller exists on the adventure bike —
  mapped to the same actions as an accelerator, never the only path.
- Touch targets huge (~80–100px min) and few. Nothing destructive adjacent to anything
  frequent.

## Glance hierarchy (from the ride)

1. **The map** — terrain and corners coming up. The map *is* the app.
2. **Next turn** — audio first (1 beep = right, 2 beeps = left), screen is confirmation.
3. **Speed** (adventure bike) / **battery-range** (Stark) — profile-dependent.

Everything else is hidden-until-needed or stopped-only.

## Section 1 — Ride view

Map full-bleed, edge to edge. Nothing opaque except the three interactive elements;
all else is translucent overlay.

**Overlays (glance-only, non-interactive):**

- **Centre stays clear** — top-centre is where the trail ahead renders. Nothing is ever
  centred.
- **Battery** on one edge: small graphic + percentage ("63%"). **Mode** as a single digit
  on the opposite edge (Stark profile). Adventure profile: **speed** takes the battery slot.
- At 720×720 the mode digit auto-fades 4s after any change; battery persists. Wide screen
  keeps both resident.
- **Turn strip** (existing slim top bar): text detail — "→ Bathurst St" — only when a turn
  is in audio range.
- **Giant turn arrow**: solid yellow arrow up to ~¼ screen, anchored on the side of the
  turn (right arrow hugs right edge, left hugs left). Readable in peripheral vision.
  **The same symbol flashing = indicator on** (from telemetry). One visual vocabulary.
- **Turn countdown borrows the main number slot**: on turn approach the profile's
  primary number (speed on adventure, battery on Stark) is temporarily replaced by
  distance-or-seconds to the intersection (existing setting, incl. freeze-at-last-value
  when stopped), styled in turn amber to match the arrow so it can't be misread as
  speed/battery. Primary number returns after the turn. Zero new resident elements.

**Interactive elements (exactly three):**

1. **The map** — clean single tap → TURN MODE; tap again → previous zoom.
   Pinch/drag disabled above walking speed (manipulation is a stopped activity).
2. **The dot** — tap: centre on me · second tap: whole route · hold: lock-to-centre.
   Locked state shown as a ring; any manual drag (stopped) breaks the lock.
3. **☰ Menu** — replaces the whole screen with a tile grid (Section 3).

**Camera rules:**

- Auto-zoom on approaching turns stays, but any manual zoom-out during it is respected
  immediately and suppresses re-zoom for that turn. No fighting a stuck camera.
- **North-up look-ahead:** with hold-north on, the position dot drifts slowly opposite
  the direction of travel (heading south → dot migrates toward top of screen) so the map
  ahead always gets the biggest share of screen. Track-up uses a fixed low-third placement.
- 720→1440: identical concept; the wide screen spends its extra width on map look-ahead,
  never on a second column of widgets.

## Section 2 — TURN MODE

The signature interaction, for unmarked intersections. One clean tap anywhere on the map:

- **Camera:** snap zoom tight (~z18), rotate compass-up to heading, rider centred
  low-third so the intersection fills the view ahead.
- **Shown:** track line(s) through the junction bolded, heading vector, any existing
  turn point.
- **One big button: MARK TURN** (bottom, glove-sized).

**Turn-point editing — one-tap grammar, all inside this view:**

- **MARK TURN** → drops a point at the nearest track position, arrowed with exit heading.
- **Tap an existing point** → removes it. If it was driving an auto-zoom, zoom back out
  ("this turn is obvious, stop telling me").
- **Tap elsewhere after removing** → point re-places there (move = delete + place).
- Points anchor to **geometry, not track index** — an out-and-back segment carries the
  turn point in both passes automatically. Attach to all tracks sharing the segment.

**Exit:** second tap on empty map → previous zoom; or **self-dismiss** ~50m past the
junction. Never required to tap out mid-corner.

**Sync:** every add/move/delete queues as a pack contribution — pushed live to group
riders when connected, and back to the Dingo pack for everyone's next download.

**General POI marking** (hazard, camp, water, photo) is a stopped activity via the menu
(MARK SPOT), distinct from turn points.

## Section 3 — The menu

☰ replaces the entire screen with a grid of fat tiles — no panel-over-map compromise.
The menu borrows the whole screen and gives it back.

- **Grid:** 3×3 at 720×720 (~230px tiles); same tiles, larger/spaced, at 1440×720.
- Tap tile → act → close. ☰ again or empty space → close, no action.
  Auto-close after ~8s untouched.
- **Ride tiles:** MUTE (state on tile) · MARK SPOT · ZOOM presets (pinch is disabled
  moving) · LAYERS · the secondary number (tap to swap which number owns the edge slot) ·
  START/STOP.
- **Idle tiles:** START/STOP, track/pack picker, ride profile, settings, export,
  DEMO (see Later).
- **START/STOP is one toggle tile, plain tap, no hold-to-stop ring** — the menu is
  already a deliberate two-tap path, so accidental stops can't happen. Delete the
  hold-ring code.
- **Two-deep maximum:** a tile acts instantly or opens exactly one full-screen picker
  (LAYERS → grid of layers). Never three levels. Deeper tuning belongs to the workshop.

## Section 4 — Telemetry & the wide screen

Telemetry is the real-estate unlock — first-class in this overhaul, not a later phase.
Verified WebSocket map already covers: battery, mode, reverse, crawl, horn, indicators.

- **Battery/range:** resident edge element (Stark profile).
- **Mode:** resident single digit on the opposite edge (auto-fades at 720×720).
- **Mode change → HP / Regen / TC card** flashes ~4s then vanishes (existing
  flash-card pattern, kept). Reverse/crawl: same event-driven brief badge.
- **Indicators:** the flashing giant yellow arrows — no new element.
- Nothing else telemetry-related occupies resident pixels.

**Ride profiles stay minimal:** *Adventure* vs *Stark* — which number is resident,
whether telemetry tiles appear in the menu. Two presets, not a settings sprawl.

## Section 5 — The workshop (settings registry)

The "sister settings app" idea, kept in its healthiest form: right about *what*
(a database of every tweakable, with exposure flags), wrong about *where* (a separate
app duplicating the UI would drift and lie; and it would not make DingoNav faster —
settings UI is inert DOM, not the perf cost).

- **Settings registry:** one table defining every tweakable — track width, colours,
  arrow size, beep counts, zoom presets, fade timings… — each with type, range, default,
  and exposure flags: `normal | advanced` and `menu | settings | hidden`.
- **Settings screens are generated from the registry** — no more hand-wired controls
  per setting.
- **Config export/import as a file.** Bench-tune on a desktop browser at 1440×720 in the
  same app with live preview, export, ingest on the bike. The sister app's whole value,
  zero duplicated code, and the preview can never lie.
- Registry flags promote/demote settings between normal/advanced without touching UI code.

## Later (noted, not in this build)

- **DEMO mode** — a panel tile that helps users understand the app: speed up the UI,
  jump to a particular part of the track, and optionally scripted panel-button replays
  showing how everything hangs together, narrated by voice, text, or both.
- Group live sync transport (turn points already queue for it).

## Build order (suggested)

1. Ride view rebuild: full-bleed map, three elements, edge numbers, giant arrows,
   camera rules (zoom-out respect, north-up drift).
2. TURN MODE + turn-point grammar (local only).
3. Menu grid rework (START/STOP toggle, two-deep rule).
4. Telemetry residents + indicator arrows + profiles.
5. Turn-point pack sync.
6. Settings registry + generated settings + config export/import.
