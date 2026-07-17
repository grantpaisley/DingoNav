# Route appearance & nav gestures — design draft

**Date:** 2026-07-17
**Status:** VALIDATED 2026-07-17 (option-based grill, four batches + follow-ups).
All questions resolved. Supersedes parts of the 2026-07-13 route-rendering
design (§3) and the 2026-07-15 ride-UI gesture grammar where noted in §8.

## 1. Route line system

### 1.1 Colour tokens

| Role | Value | Note |
|---|---|---|
| Active route core | `#4AA8FF` | **DECIDED** — replaces cyan `#00e5ff` as the `colRoute` default; stays a registry colour setting |
| Active case, option A | `#FFFFFF` | |
| Active case, option B | `#101820` | |
| Travelled route core | `#7F8791` | neutral grey |
| Travelled route case | `#1A1E24` | near-black |

**DECIDED (was Q2):** shadow/glow is **the casing colour swap, nothing more** —
dark case `#101820` by day (reads as shadow), white case at night (reads as
glow), driven automatically by the existing day/night style flip. No extra
effect layers. The A/B "choice" is therefore automatic; keep a registry
override (auto | always-white | always-dark) for tuning. Single casing layer —
the "dark + narrow white rim" double-casing reading of point 15 is rejected.

### 1.2 Widths

Default overall width 6 px, core 4 px (case = 1 px per side). Settings (registry):

- **Overall width** — number input; core scales to keep the case:core ratio.
- **Zoomed-in width** and **zoomed-out (full-track) width** — the two ends of the
  zoom interpolation.
- **Case:core ratio** — adjustable.

Reference table (Grant's):

| Zoom / use | Core | Total |
|---|---|---|
| Full-track overview | 4 px | 6 px |
| Planning / mid zoom | 5–6 px | 7.5–9 px |
| Turn-by-turn navigation | 6.5–8 px | 10–12 px |

**DECIDED (was Q3):** plain zoom interpolation between the two knob values —
nav zoom levels land at the fat end naturally; no per-state width switching.

### 1.3 Surface patterns (per screenshot)

- **Sealed** — solid
- **Track / dirt road** — dashed
- **Single** — dotted

Same mapping as today (`surf-dirt` dashed, `surf-single` dotted). Patterns are
preserved in the travelled section so a rider reversing direction can still read
surface. Dash/dot gaps stay fully transparent.

### 1.4 Route states

| State | Core | Case | Effects |
|---|---|---|---|
| Remaining | 100% saturation/opacity | single case: dark (day) / white (night) — decided, see 1.1 | "shadow"/"glow" = the case colour itself |
| Recent (last 50–100 m behind) | 70–85% strength | keeps clear connection to position marker | |
| Older travelled | grey `#7F8791`, 45–60% opacity | reduced `#1A1E24` | flat — case does not swap day/night |
| Missed (after rejoin) | core colour at ~50% opacity | **none** | registry-tunable opacity |

**Turn-point markers follow the line treatment** (decided 2026-07-17): grey on
travelled sections, dimmed to ~50% on missed sections, full strength ahead.

- Travelled section keeps surface patterns (see 1.3).
- Completed uphill chevrons are removed/neutralised in the travelled section —
  only upcoming hazards command attention.
- **DECIDED (was Q5):** recent band = last **75 m at 80% strength**; older
  travelled at **50% opacity**. All three registry-tunable.

### 1.5 Off-route rule (missed segments stay hot)

Progress advances by **route sequence index, not nearest geographic point**.
While off-track the index does not advance and the skipped span stays full
colour (you may still come back for it). **On rejoin the missed span drops to
~50% opacity with its casing removed** (decided 2026-07-17) — casing is the
exclusive "route ahead" signal, giving three glance-ranked weights:
remaining (full colour + case) > missed (half colour, bare) > travelled (grey).
Rationale: near a returning leg you must distinguish the in and out tracks.
Missed spans stay identifiable post-ride as the bits you skipped.

**DECIDED (was Q6):** progress state **persists past STOP** — travelled-grey +
full-colour missed spans stay on the map for post-ride review, cleared when a
new navigation starts (same lifecycle as the breadcrumb trail).

### 1.6 Layering (self-crossing / out-and-back)

Draw order bottom→top: travelled route → remaining route → position marker
(dot/square). On an out-and-back the outbound (travelled, grey) sits beneath the
inbound (remaining, colour). Position marker always on top.

**DECIDED (was Q7):** both render. Travelled-grey shows *route progress*; the
muted dotted breadcrumb (`S.trail`) shows *where you actually went*, sits
**under everything** in the stack, and earns its keep exactly where the two
diverge — off-route wandering. Full order bottom→top: breadcrumb → travelled
route → remaining route → position marker.

### 1.7 Track ends

**Big dot at the start of the track, arrowhead at the end** (as in screenshot).
These are structural orientation marks, not progress marks: unlike turn-point
markers they do **not** grey out — they stay at full strength through every
route state and **persist in the post-ride view**, so a finished ride still
reads start-to-end at a glance (the mock-up's travelled grey/black lines keep
the blue dot and the arrowhead). They apply to the navigated route and to an
archived ride when shown individually (§1.8); dot/arrow scale with the line
width.

## 1.8 Breadcrumb lifecycle & ride archive (decided 2026-07-17)

Today the heatmap is fed only by imported bundles — the bike never contributes,
and the breadcrumb is discarded when the next navigation starts. New rule:

- **On STOP: archive the ride.** Simplify the trail (Douglas-Peucker, ~10 m
  tolerance, tunable) and append it to a local rides store (IndexedDB, dated,
  named after the navigated track).
- **Archived rides render as 'own rides'** in the existing heat layers
  (`clsMatch` already colours class `own` `#ff7a00`) — trails you've actually
  ridden go solid orange organically, no Dingo web round-trip required.
- **Each archived ride exportable as GPX** (menu, stopped-only).
- **Live breadcrumb keeps its current lifecycle** — visible after STOP for
  review/backtracking, cleared when the next navigation starts.
- Build detail to resolve later: when a newly ingested bundle already contains
  an archived ride, dedup (by date) or accept the double-draw.

## 2. Slope chevrons & direction notches

**This repurposes the chevron glyph.** Today `sel-chevrons` (`›` symbols) encode
*direction*. New scheme:

- **Chevrons = steep / very steep slope warnings** (two severity levels).
  Removed/neutralised once the section is travelled.
- **Direction = V-shaped chunks cut out of the track line** (notches), replacing
  the direction chevrons.

**DECIDED (was Q9):** the colour-=-steepness gradient channel **dies entirely** —
delete the `steep` setting, grade-band baking, and the line-gradient path
(2026-07-13 §3). One flat core colour always; slope chevrons are the only grade
signal.

**DECIDED (was Q10):** direction marks are **case-coloured V overlays** drawn on
top of the line (same symbol-layer mechanism as today's chevrons, restyled as
V's in the casing colour) — not true cutouts. Reads on solid, dashed and dotted
segments alike.

**DECIDED (was Q8):** single chevron **≥10%**, double chevron **≥17%** grade
(registry-tunable). Chevrons point uphill, drawn in the casing colour.

## 3. Turn arrow

Giant nav arrow stays as-is (shape/size/behaviour, incl. indicator-flash reuse).
Add registry options for **fill colour** and **surround/outline colour**.

## 4. Chrome: day theme, hamburger, typography

- **Day theme is Mac-like** (samples review, 2026-07-17 second pass — supersedes
  the earlier ☰-always-dark and panel-scope answers):
  - Plates (controls, ☰, dot/square): `#f5f5f7`, hairline `#c9c9ce`, dark glyphs
    (15:1). The ☰ visibility requirement is met by contrast, not darkness.
  - Speed/mode readouts: near-black `#15202b` with a light halo (white failed
    1.8:1 on day maps); countdown amber darkens to `#b45309` by day.
  - Accent: **macOS blue `#007AFF` by day** (cyan fails 1.4:1 on light), cyan
    `#00e5ff` at night — swapped via `body.daymode`, mirrored by hand in canvas.
  - Panel: full Mac light component pass (white buttons + hairlines, blue
    selected segs, green iOS-style switches) — light by day, original dark at
    night.
  - Turn strip: frosted white by day, dark translucent at night.
  - **No riding fade on day styles** (`--navOp:1`); night keeps the 0.4 ghost.
  - Route dash gaps read as the **casing colour** (continuous case); single
    track = dense square dashes, not dots. `Dash gaps` seg restores see-through.
- **Text mixed case everywhere** (kill ALL-CAPS incl. tile labels), **symbols
  ~12% larger**.
- New app versions **replace saved UI layout config** (v4 migration; silent for
  now, a later version may warn), and layout anchors clamp into the viewport.

## 5. Nav gestures — DECIDED grammar (was Q13; supersedes 2026-07-15 §1/§2 triggers)

**Double-tap is the mode toggle:**

- **Double-tap (riding view) → TURN MODE**: snap zoom in, compass mode,
  MARK TURN button shown. Dot icon changes to **square** (you are centred).
- **Double-tap (in TURN MODE) → back to riding zoom.**

**Dot/square is one stateful re-centre button** (merges ● and ▢):

| State | Icon | Tap does |
|---|---|---|
| Centred on rider | **square** | zoom out to full track |
| Panned away (any drag) | **dot** | re-centre → becomes square |

- Sliding the screen pans (looking around at zoomed-in level); the instant a
  scroll starts, square → dot.
- Drag pans at any time; **pinch-zoom only when stopped**.
- Full cycle: double-tap → TURN MODE (square) → drag to look around (dot) →
  tap dot to re-centre (square) → tap square for full track, or double-tap
  back to riding zoom.
- Hold-to-lock (2026-07-15 dot grammar) is **dropped** unless it resurfaces.

**Marking a turn (two-step, armed placement):**

1. Tap **MARK TURN** (arms placement; prompt: "tap to place marker").
2. **Tap to place — DECIDED (was Q14).** Long-press rejected (gloves +
   vibration); a stray tap costs one tap to fix (tap a point to delete it —
   the 07-15 delete/move grammar stays). Placement snaps to nearest track
   position.

**Mode digit is tappable (resolved Q15):** tapping the resident Stark mode
digit replays the **HP / Regen / TC info card** — the same ~4 s flash card
shown automatically on a mode change (2026-07-15 §4). No new UI, just an
on-demand replay of the existing card. (Original gesture item 8 was empty —
dropped.)

**DEMO simulates Stark mode:** the demo ride also feeds simulated Stark mode
telemetry, so the mode digit, mode-change flash card, and tap-to-replay can be
exercised off the bike.

## 6. Audio grammar

Direction = count (unchanged: 1 = right, 2 = left). **Phase = pitch** (new):

| Event | Right | Left |
|---|---|---|
| Approach | single **deep** tone | double **deep** tone |
| At turn | single **high** tone | double **high** tone |

- Replaces the direction-less 660 Hz `far()` beep — approach becomes directional.
- **DECIDED (was Q16):** deep = **460 Hz**, high = 990 Hz (both registry-tunable).
- **Approach and departure chimes**: settings for trigger by **seconds or
  distance** (per chime). **DECIDED (was Q17):** departure = **turn-complete
  confirmation** — a short neutral chirp N s/m after exiting the junction
  on-route ("turn done, carry on"), reusing the back-on-track sound family;
  distinct from the off-track alarm.

## 7. Turn instructions

- **Tap the header/turn strip → briefly expands the instruction (~4 s), then
  collapses.** **DECIDED (was Q18):** accepted exception to the exactly-three
  rule — the strip only exists during turn approach and the tap is read-only.
  Rule becomes "three, plus the turn strip when present".
- Instructions in mixed case, surface-aware naming:
  - Named road: "Left on to Arcadia Rd"
  - On to singletrack: "Left on to Single Track"
  - Sealed → dirt: "Left on to dirt"
  - **DECIDED (was Q19):** neither name nor surface change known → bare
    "Left" / "Right".

## 8. Conflicts with prior designs (explicit supersessions)

| Prior decision | This doc |
|---|---|
| 2026-07-13 §3 "No outside lines" — casing deleted, same-colour halo | **Casing reinstated** (auto day/night); halo system dies — delete the six `*-halo` layers and `haloOp`/`haloMul` knobs (**decided, was Q20**) |
| Colour = steepness gradient channel | **DEAD (decided)** — fixed core colour `#4AA8FF` + slope chevrons; delete `steep` setting & gradient path |
| `colRoute` default `#00e5ff` cyan | **`#4AA8FF` (decided)** — still a registry colour setting |
| `sel-chevrons` = direction | Chevrons = steepness; direction = **case-coloured V overlays (decided)** — not cutouts |
| 660 Hz direction-less far beep | Directional deep-tone approach |
| 1-tap map = TURN MODE; dot tap/tap/hold grammar | **Double-tap = TURN MODE toggle + dot/square state button (decided, §5)**; hold-to-lock dropped |
| MARK TURN one-tap drop | Arm (MARK TURN) then place (**Q14 narrowed** — tap vs long-press to place) |

## 9. Registry additions (settings, from this doc)

Route: overall width, zoomed-in/out widths, case:core ratio, case colour
(auto | always-white | always-dark; default auto day/night), core colour
(default `#4AA8FF`), travelled opacities (recent 80% / older 50%), recent-band
length (75 m), missed-span opacity (default 50%). Arrow: fill, surround. Chevrons: grade thresholds (10% / 17%),
size. Direction Vs: spacing, size. Audio: deep (460 Hz) / high (990 Hz)
frequencies, approach chime (seconds|distance + value), departure chime (same).
Chrome: ☰ plate opacity. Header: expand duration (~4 s).

Deletions: `steep` setting + grade-band/line-gradient path; six `*-halo` layers
+ `haloOp`/`haloMul`; hold-to-lock dot gesture.

## 10. Build order

1. **Route line system** — casing layers (auto day/night), widths + knobs,
   `#4AA8FF` default, halo/gradient deletion. Pure rendering, no state model.
2. **Progress model** — sequence-index progress with span tracking (travelled /
   missed / remaining), persistence past STOP, layering over breadcrumb.
3. **Travelled/recent styling** — grey + fades + preserved patterns, chevron
   neutralisation on travelled sections.
4. **Direction Vs + slope chevrons** — restyle `sel-chevrons` into the two new
   symbol layers.
5. **Gesture grammar** — double-tap TURN MODE toggle, dot/square button,
   armed tap-to-place marking.
6. **Audio** — directional deep/high grammar, departure chime, chime settings.
7. **Chrome & telemetry taps** — ☰ plate, day panel theme, mixed case + icon
   size, header expand, arrow colour options, mode-digit tap → flash card
   replay, demo Stark-mode simulation.
8. **Ride archive** — STOP → simplify breadcrumb → local rides store → own-rides
   heat layer + GPX export (§1.8).
