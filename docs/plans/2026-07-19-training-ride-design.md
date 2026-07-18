# Training ride — interactive in-app tutorial

*2026-07-19. Realizes the "DEMO mode" Later item from
[2026-07-15-ride-ui-overhaul-design.md](2026-07-15-ride-ui-overhaul-design.md).*

## Purpose

New riders (mates receiving a shared pack) learn DingoNav by *doing*: a
simulated ride that pauses at teaching moments and asks for the real gesture —
double-tap, drag, dot, ☰ tiles — advancing only when the learner performs it.
Text cards + the real beeps; no TTS, no video file. Works with nothing loaded.

## Decisions (validated)

- **In-app interactive training ride**, extending demo mode. Not an MP4.
- **Text callout cards + real BEEP cues.** No spoken narration.
- **Do-the-action to advance**; passive phenomena (beeps, banners) are
  watch-then-ack. "Can't do this here — skip" link on gesture steps.
- **Launch:** starting a demo (☰ `#gDemo` or settings `#demoBtn`) opens a
  chooser — *Training ride* vs *Plain demo*. Plus a **"Try the training ride"
  button on the empty home screen** (`refreshEmpty`). No new glove tile.
- **Training route ships as an inline constant, not a `.dingonav`.** The real
  ingest path purges loaded packs (`purgeAllPacks`), clobbers the `basemap`
  IDB singleton, and wants a reload — unacceptable risk for a tutorial.
  Inline route (~3.5 km, ~220 pts + pre-baked cues, ~10-12 KB in index.html)
  sits inside the auto-downloaded Central Coast basemap so new users get real
  imagery; still fully functional on the dark fallback. Never touches IDB,
  never appears in track lists, removed on exit. `make_bundle.py` untouched.
- **Setup & packs = 3 pre-ride cards** before the sim starts, then one
  continuous ride.
- **No perf cost:** all training code is inert unless `TRAIN.active`.

## Architecture

### Engine (new section beside demo mode, ~line 3636)

- `TRAIN` state: `{active, i, holdD, offT, prevSel, prevSound}`.
- `TRAIN_STEPS`: one hardcoded array. Step shape:
  `{at, ride, title, html, target, advance: {ev|ack}, before(), after()}`.
  `at` = sim distance trigger (`-1` = pre-ride card, `null` = chained
  immediately after previous step). `ride:true` = card without pausing
  (off-track act).
- **Pause semantics:** the demo `setInterval` never stops. Paused = hold `d`
  at `TRAIN.holdD` and feed the same fix with `speed = 0` — the app genuinely
  reads "stopped", so `applyMoveGestures` re-enables pinch (the real
  stop-and-manipulate grammar). `avgSpd` EMA untouched (spd>1 guard), warn
  distances don't decay.
- **Event taps:** one-line `trainEvent('x')` appended to 11 existing
  handlers: `enterTurnMode`/`exitTurnMode`, `dragstart`, `zoomend` (gesture),
  dot-recentre, `setLock`, `presetTap`, `setSound`, `openGlove`,
  `northBtn`, off-track/back-on transitions in `onFix`. No wrapping.
- **Off-track act:** `TRAIN.offT` ticks displace the fix ~90 m perpendicular
  to the local heading (past `offM` 60) so the real banner + `BEEP.off` fire;
  expiry returns inside `onM` 40 → real `BEEP.back` → advance.
- Orchestration: `startTraining` / `trainCheck(d)` / `trainShow` /
  `trainAdvance` / `endTraining(finished)`. Dev hook `window.__trainGoto(n)`.
- `stopDemo` calls `endTraining(false)` if active — every exit path
  (✕, ☰ Stop, demo toggle, track end) funnels through cleanup.

### Guards (one line each)

- `friendPub`: never broadcast sim positions while training.
- `gloveArm`: no 8 s auto-close while a card targets a glove tile.
- `refreshTrackList`: skip `t._training`.
- `startTraining` pre-seeds `S.set.seenZoomTip` (kills `zoomTipGate` collision).
- `endTraining`: restore sound if mute lesson abandoned; `S.trail = []`
  before `stopNav` (defeats `archiveRide`); remove `__training` track,
  restore previous selection. Mark lesson is describe-only (no real
  `markSpot` — would queue live turn edits).

### Card UI

`#trainCard` fixed bottom-centre, `min(70vw, 400px)`, z-index 27 (above the
glove overlay's 25 so tile-targeting cards stay readable), reusing the `#dlg`
palette. Top row: "lesson n/14" + "✕ end training". Buttons: "Got it" (ack
steps) / skip link (ev steps). **No backdrop shade** — the map must stay
touchable for gesture lessons. Spotlight = `.trainSpot` class on the target:
accent box-shadow + 1.2 s pulse. Must clear `#dotBtn`, `#menuBtn`,
`#progress`, and the big arrows at both 1440×720 and 720×720.

### Training route

- `TRAIN_PTS` (~220 `[lat,lon]`, 5 dp) — a real ~3.5 km loop with ≥5
  junctions inside `central-coast.pmtiles` coverage (map default centre
  [151.3, −33.3]).
- `TRAIN_CUES` — baked cues authored via the dev-console path
  (`window.__cue.cues` after loading the same points as GPX), plus one
  hand-added danger mark. Baked cues mean `startNav` skips `analyzeRoute`
  entirely — no tiles required for the nav logic.
- `buildTrainingTrack()`: `processTrack('__training', …)`, set
  `_training`, `baseCues`, `applyCueOverlay`. In-memory only.
- REF projection skew for users anchored far from NSW is cosmetic
  (HUD metre readouts only); sim is self-consistent. Comment in code.

## Lesson sequence (14 top-level steps)

Warn maths at 8.5 m/s enduro: approach ≈ 127 m out, turn-now ≈ 42 m,
countdown strip 300 m, danger barks 200/50 m.

1. *Pre-ride* — welcome; beeps-first navigation; turn sound up. (ack)
2. *Pre-ride* — packs: one `.dingonav` from Dingo = tracks + offline maps;
   re-download lives on the home screen. (ack)
3. *Pre-ride* — beep grammar: **1 = right, 2 = left; deep = coming up,
   high = turn now**; `before()` plays samples. (ack)
4. `at:60` — screen tour: HUD strip, progress bar, speed. (ack)
5. `T1−170` — listen to a real approach→turn cue + giant arrow. (ack, passive)
6. `T1+70` — the rising two-note done-chime. (ack)
7. `T1+250` — drag to look around (always live). (ev drag)
8. chained — tap the dot to snap back. (ev recentre)
9. chained — you're "stopped": pinch/wheel zoom works; above walking speed
   finger-zoom locks, ± always works. (ev zoom-gesture + skip)
10. chained — tap ☰: whole screen becomes glove tiles. (ev glove)
11. chained — Mute, then un-mute (danger still barks). (ev unmute)
12. chained — Zoom close / Zoom wide presets; hold-to-set. (ev preset + skip)
13. `T2−40` — **double-tap = TURN MODE** at a real fork; chained card
    describes ADD MARK; double-tap again to exit. (ev turnmode →
    turnmode-exit)
14. `T2+200` — scripted off-track: growl + red banner, return chirp; note
    reverse-direction auto-flip. Then centre-lock long-press (ev lock +
    skip), danger barks (ack, passive), finish card → `endTraining(true)`.

## Build order

1. Engine core: state, `trainEvent` taps, pause/feed/offset in `startDemo`,
   orchestration, `__trainGoto`. Verify with 3 placeholder steps.
2. Card UI + spotlight at both viewports.
3. Route + cues: author loop, bake `TRAIN_PTS`/`TRAIN_CUES`, set `at:` values.
4. Launch flow (`#demoPick` chooser, `#gDemo`/`#demoBtn` rewire, empty-state
   button) + guards.
5. Content pass: full card text.
6. Verification; bump `sw.js` CACHE v22 → v23.

## Verification (desktop, `node serve.js` :8138)

- Fresh profile (clear IDB + localStorage), both viewports: empty state →
  training via home button and via ☰ → Demo → chooser. Complete every step
  with real mouse gestures (dblclick, drag, click, 600 ms hold, wheel);
  pinch step exercises the skip link.
- During pauses: speed reads 0, HUD frozen, wheel zoom works; on resume
  beeps fire; off-track step shows/clears `#banner`.
- Exit mid-lesson via ✕: sound restored, no `__training` in tracks, previous
  selection restored, no ride archived, reload → identical track list.
- Plain-demo regression: unchanged behaviour incl. Stark sim ticks.
- Card geometry at 720×720: clears dot/☰/progress/arrows; card readable
  above the open glove overlay.
