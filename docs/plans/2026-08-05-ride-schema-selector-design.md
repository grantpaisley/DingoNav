# Ride schema selector — Studio preset pairs in the glove menu

2026-08-05. The DingoNav side of the scheme importer/switcher anticipated by
pack v2 (`pack.schemes`) and specified in the Dingo Studio design
(`Dingo/Docs/plans/2026-08-02-dingo-studio-design.md`) and the behaviour
framework (`DingoStudio/docs/2026-08-03-nav-behavior-framework.md`).

## Entry

The ☰ glove grid's **Mark spot** tile is now **Schema** (palette icon).
`markSpot()` stays — friend/pack `spot` sync still lands via the inbox — only
the tile changed. The tile opens a full-screen selector with two sections:

- **Look — `.dingoscheme`**: Dingo default · Google Maps · Waze · Locus Map ·
  OziExplorer · DMD2
- **Behaviour — `.dingobehavior`**: Matched ⛓ (default) · Dingo default ·
  Google Maps · Waze · Locus · DMD2

Tapping a Look tile applies that scheme plus its same-id behaviour while
Behaviour is on "Matched" (Studio's profile-pairing semantic). A Behaviour
tile pins that behaviour explicitly — mix-and-match. "Dingo default" for a
facet means factory: no scheme mounted / no behaviour overrides.

## Overwrite semantics

Applying a schema is **reset-then-apply**: `S.set` (including every `adv`
slider, zoom presets, layout) returns to factory defaults — `factorySet()`,
the one source of truth extracted from the old `S.set` literal — then the
preset's mappings land on top. Deterministic, no merge, no confirm.

Surviving the reset (`SCHEMA_KEEP`): identity (`name`, `email`, ride `code`,
`codeAuto`), controller `keys`, Varg pairing, `aerialUrl`, the one-time
stamps (`seenIntro`, `seenZoomTip`) and migration flags (`_v2`–`_v5`,
`_packCfg`).

## Preset files & appliers

`schemes/*.json` + `behaviors/*.json` are vendored from DingoStudio and
SW-precached (CACHE v67) — the selector works fully offline.

The scheme applier is the vendored canonical `applier-nav.js` translated to
Nav's runtime names:

- basemap tokens → a dynamic `MAP_STYLES.scheme` entry (base flavour picks
  `layers.json`/`layers-light.json`, per-layer paint overrides splice into
  `buildStyle()`, `__labels` sentinel patches every symbol layer, hillshade
  paint from the tokens). The style cycle collapses to schema ↔ satellite
  while a schema is active; `isNightStyle()` reads the schema's base.
- overlay tokens → `adv` knobs (`colRoute`, `colOwn/Plan/Other`,
  `routeWOut/In`, `caseMode`, `colDone`, `chevSize/Gap`, breadcrumb→`colCrumb`)
- mark tokens → the `MARKS` colour table (factory snapshot in `MARKS_D`)
- hud tokens → the `--bg/--panel/--fg/--dim/--accent/--ok/--warn/--bad`
  (+ heat) CSS variables

The behaviour applier maps only params with Nav homes today: `followMode`→
`orient`, `autoZoom`, `easeMs`, `approachSecs/Mul/FloorM`→`apprS/Mul/Floor`,
`offroute.detectM/rejoinM`→`offM/onM`, `breadcrumb(SpacingM)`→`trail`/
`trailGap`, `voice.mode: silent`→sound off, and the zoom curve's span ends →
the vehicle's zoom presets. `reroute.*`, `pitch`, lane guidance, TTS are
skipped per the ignore-unknown contract.

## Persistence & failure

The applied ids + validated JSON persist as one IDB record (`id: 'schema'`).
Boot re-mounts the look (CSS vars, mark colours, style entry) before the
first `buildStyle()` — no default-style flash; the settings half already
lives in `S.set`. Contract handling: `schemaVersion` major ≠ 1 rejects at
apply; a stored schema that fails to mount at boot unmounts, falls back to
the factory look and says so — a bad schema never bricks Nav. Day tokens
only for now (`night` overlays resolve when Nav grows a day/night schema
mode).
