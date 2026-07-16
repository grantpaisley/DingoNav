# Map Appearance Mock-up — Design

**Date:** 2026-07-16
**Trigger:** The settings registry (overhaul step 6) made every tweakable a table row — but
map *appearance* tuning (track lines, heatmap, basemap loudness, per-style differences) is
still blind: sliders in a panel, effects judged later on a ride. Grant wants a dedicated
page to explore combinations visually, with Mac-grade aesthetics, before the result is
folded back into the app.

## Purpose & fidelity

**Design exploration first.** A standalone page to find the ideal tuning UI and the
winning colour/line combinations. Once validated, it becomes the blueprint for a real
"Appearance" surface wired into the settings registry — the page itself never ships in
the PWA.

- One self-contained file: **`mockups/map-appearance.html`** (new folder; mock-ups never
  ship with the app). Zero dependencies, double-click to open, fully offline.
- State persists in `localStorage`; **Reset** and **Copy theme** always available.

## Layout — Mac inspector

Keynote/Final Cut pattern; the preview is the point.

- **Map preview is the hero**, filling the window edge to edge.
- **Right-hand inspector** (~340px): translucent (`backdrop-filter` blur over the map),
  system font stack, 13px controls, hairline separators, macOS-style switches, native
  colour wells, sliders with value readouts, animated disclosure groups. Light chrome —
  it should feel native next to Finder, not like the PWA.
- **Segmented control floating top-centre**: Day / Trail / Dark / Sat. Re-skins the whole
  scene instantly; flicking through all four is how a theme is audited.
- **Resolution switcher** beside it: **Full window / 1440×720 / 720×1440 / 720×720** —
  the dash's landscape, portrait, and half-screen modes. The preview letterboxes to the
  chosen frame at ride zoom (scaled to fit, true aspect), so a theme is judged on the
  pixels the Varg dash actually gets.
- **▶ Ride** button bottom-left of the preview (ride simulation, below).

## The fake map — one scene, four skins

Hand-authored **SVG** scene (restyle = CSS variable swap, no redraw code) mimicking each
basemap style:

- **Day** — light paper, soft bushland greens, brown minor trails, subtle hillshade,
  grey roads, muted Central-Coast-flavoured labels.
- **Trail** — same geometry, high-contrast skin, trails loud orange (like the current
  contrast style).
- **Dark** — near-black ground, dim blue-grey roads. **Known problem: currently too dark
  to see anything** — the Basemap adjusters below exist to fix exactly this.
- **Sat** — faux imagery (mottled green/brown gradients, road labels only) — the style
  where cyan routes historically die.

**Staged for honest judgement** — every hard case from real rides, nothing decorative
that can't be tuned:

- Route crosses and briefly *shares* a heatmap corridor (knockout + under-route opacity
  visible).
- All four surface classes on one route: sealed lead-in → dashed dirt climb → dotted
  singletrack switchbacks → unmapped valley.
- A tight switchback cluster (dash patterns at their worst), a straight fire-road run
  (chevron spacing), a junction where a basemap trail forks off the route ("which line am
  I following?").
- Heatmap spaghetti: own + others + planned converging near the junction.
- **Ride chrome overlaid, always**: position arrow mid-route, breadcrumbs behind, ridden
  portion dimmed, battery "63%" + mode "3" edge readouts, giant turn arrow ghosted at an
  edge, zoom/dot buttons at ride opacity. A bare-map preview flatters every colour choice;
  the acid test is map + chrome together.

## Settings model — global + per-style pins

Demonstrates the data model the registry adopts later:

- Every control edits the **global** value by default.
- A small **pin dot** beside each control forks that one setting for the currently shown
  map style only (control gains a subtle tint = "differs here"). Unpin reverts to global.
- Tune once; override only where a style fights you.

## Inspector groups

**Theme bar** (top): preset dropdown (baked presets + "Custom") · **A/B compare**
(snapshot two candidates, flick between) · **Copy theme / Paste theme** · Reset.

**Route** — two-part lines (proper cartographic casing, not just a glow):
- **Casing**: on/off · colour · edge width each side · opacity · style hard-outline ⇄
  soft glow (subsumes today's halo). White casing = the survives-any-background trick.
- **Core**: colour · width · per-surface patterns (dirt dash length/gap, singletrack dot
  length/gap, unmapped treatment) — inspector swatches render casing+core **as a pair**
  (e.g. white outside / dark-blue dash core).
- **Ridden vs ahead**: dim strength for the ridden portion + a recolour-instead-of-dim
  alternative.
- Direction chevrons: size (0 = off) · spacing · colour.
- Default core candidate: **cyan** (nothing natural is cyan; never collides with terrain
  or heat). When steepness colouring owns the core, the casing stays — track silhouette
  survives mid-gradient.

**Heatmap** — per class (**Own / Others / Planned**): colour · width · opacity; plus
knockout-along-route radius and under-route opacity.

**Basemap** — ground brightness · road & trail brightness · label intensity · minor-trail
colour + width×. All pinnable per style; Dark will clearly want its own.

**Controls & readouts** — button opacity + size · readout size + sun-plate on/off · the
single **turn accent** (giant arrow + turn strip + countdown share one colour) · position
arrow colour/size · breadcrumb colour/spacing · steepness ramp (5 grade colours as one
gradient strip). Deliberately NOT a full button-theming system — the overhaul keeps
chrome minimal and uniform; position/size-per-element belongs to the layout editor.

**Collision guard** — wherever two must-be-distinguishable colours get too close (route
vs each heat class, route vs basemap trails, heat vs ground), a small ⚠ appears against
the offending swatches (hue/contrast distance). Informs, never blocks — trying
combinations is the point (orange-on-orange taught us this).

## Theme loop — paste, not API

A live "ask Claude" call would need a key + network in an offline file. The loop that
fits the app's DNA:

- The page defines a **theme JSON schema** (every setting incl. per-style pins).
- Grant asks Claude *in a session* for combinations ("muted earth tones, must survive
  Sat, night variant that isn't a cave"); Claude answers with theme blobs; **Paste
  theme** → compare via A/B → iterate.
- **6–8 baked presets** ship in the page, each with a one-line rationale, as starting
  points.
- **Endgame noted:** in the real app a theme is just a named preset over the same
  settings — toggleable from a seg or menu tile, carried by config export/import and
  packs for free, possibly auto Day↔Night by clock.

## Ride simulation

▶ animates the position arrow along the staged route (~20 s loop, rAF + SVG transforms):
ridden portion dims live, breadcrumbs drop, chevrons/turn accent work ahead, giant arrow
flashes at the switchback. All controls apply mid-flight — legibility is judged **in
motion**, not as a poster. Speed 1×/3× + pause. Works combined with the
resolution switcher — riding at 720×720 is the harshest legibility test. (Deferred, cut
from scope: glare simulation, extra-clutter toggle.)

## Handoff

When a theme wins: **Copy theme** → Claude translates the JSON into registry entries +
`MAP_STYLES` override tables + real casing layers in `index.html`. The mock-up stays in
`mockups/` as the living style lab.

## Out of scope

- No MapLibre, no PMTiles, no app code changes — the page touches nothing in the PWA.
- No live API calls; theme generation goes through the chat paste loop.
- No per-button theming, no layout editing (layout editor owns that).
- No dash-crop / glare / clutter toggles in v1 (ride sim only).
