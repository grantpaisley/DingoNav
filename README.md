# DingoNav

Offline GPX track follower for the bike. Separate project from
[Dingo](https://github.com/grantpaisley/Dingo) — it consumes Dingo's exports.
MapLibre GL + a PMTiles vector basemap (roads, trails, water, labels — fully offline),
with the Dingo heatmap and track overlays on top. North is always up.

## What it does

- **Offline basemap**: one `.pmtiles` file covers the whole riding area (roads, tracks,
  rivers, place labels). Auto-downloaded on first open and stored on-device (IndexedDB);
  swap areas via ☰ → *Load .pmtiles basemap…*.
- **Terrain shading**: an optional second `.pmtiles` (elevation, ~8 MB per area) adds
  hillshade relief under the trails — gullies and ridges readable at a glance, still flat
  north-up 2D so nothing about the fast-follower UX changes. Auto-downloaded like the
  basemap; toggle in settings; cut other areas with `make_hillshade.py`.
- Load **GPX tracks** + a **heatmap GeoJSON** exported from Dingo — persisted on-device,
  everything works with zero signal after first load.
- Select a track → **START** → follows you from the **nearest point on the track**, either
  direction (auto-detects reverse riding and mirrors turn arrows + chevrons).
- **Beeps on approach** to alert points, plus vibration and a big arrow + distance HUD:
  - ~160 m: single low beep (turns only)
  - ~55 m: 2× high = turn, 3× rising = hairpin, low-high = junction
- Alerts come from the track geometry (bearing change ≥45° in ~40 m) **and the heatmap**:
  anywhere another ridden trail crosses at an angle becomes a *junction* alert.
- **Off-track**: >60 m = buzz + red banner with live distance; chirp when back on.
- **Auto-zoom with speed** (fire trail = wide, singletrack = close), pinch/± zoom,
  ⛶ fit track, ◎ re-centre. Rotation is disabled — north stays up.
- **Group ride**: share the app + a ride code; riders on the same code see each other as
  green dots (ntfy.sh, ~20 s updates when online, silently off without signal).
- Wake lock while navigating; **demo mode** replays the selected track at 30 km/h.

## Files

```
index.html        the app (single file of app code)
vendor/           maplibre-gl.js/.css, pmtiles.js (vendored, no CDN — offline)
basemap/          layers.json (style), fonts/, sprites/, central-coast.pmtiles, hillshade.pmtiles
sw.js             service worker: index.html network-first, assets cache-first
manifest.json     PWA manifest (Add to Home Screen)
bundle.json       optional pre-baked tracks+heatmap, auto-loaded on first open (gitignored)
make_bundle.py    builds bundle.json from a heatmap + GPX files
make_hillshade.py cuts basemap/hillshade.pmtiles (terrain DEM) for an area
make_icons.py     regenerates the PWA icons
serve.js          tiny static server (node serve.js [port]) for local hosting
sample-data/      Central Coast heatmap export + 4 real loops (gitignored)
```

## Feeding it from Dingo

```bash
# heatmap GeoJSON (what sample-data/heatmap-central-coast.geojson is):
psql $DATABASE_URL -At -c "SELECT jsonb_build_object('type','FeatureCollection','features', jsonb_agg(
  jsonb_build_object('type','Feature','properties', jsonb_build_object('class',
    CASE WHEN origin='other' THEN 'other' WHEN track_type='route' OR started_at IS NULL THEN 'plan' ELSE 'own' END),
  'geometry', ST_AsGeoJSON(ST_SimplifyPreserveTopology(cleaned_geometry,0.00012),5)::jsonb)))
  FROM rides WHERE superseded_by IS NULL AND area_id='<AREA_UUID>' AND cleaned_geometry IS NOT NULL" > heatmap.geojson

# tracks: GPX straight from the Dingo library (Recorded/...) or `dingo export bundle`
./make_bundle.py --heatmap heatmap.geojson day1.gpx day2.gpx -o bundle.json
```

## Cutting a basemap for another area

```bash
brew install pmtiles
pmtiles extract https://build.protomaps.com/$(date -v-1d +%Y%m%d).pmtiles my-area.pmtiles \
  --bbox=<minLon>,<minLat>,<maxLon>,<maxLat>
```
The Central Coast + Watagans extract (150.85,-33.75 → 151.85,-32.85, zoom 0-15) is 33 MB.
Drop the file at `basemap/central-coast.pmtiles` for auto-download, or load any `.pmtiles`
in-app via ☰. Protomaps daily builds are OSM-derived and free (attribution included).

## Cutting terrain shading for another area

```bash
pip install pmtiles
./make_hillshade.py --bbox <minLon>,<minLat>,<maxLon>,<maxLat>   # or --basemap my-area.pmtiles
```
Downloads Terrarium elevation tiles (AWS Open Data, free, no key) at z6–12 and packs them
into a raster-dem `.pmtiles`; MapLibre renders the hillshade on-device (a cheap shading
pass — not live 3D terrain). With no arguments it reuses the bounds of
`basemap/central-coast.pmtiles` (~8 MB output). Drop the file at `basemap/hillshade.pmtiles`
for auto-download, or load any file in-app via ☰ → *Load .pmtiles terrain…*.

## Putting it on the phone

GPS + service workers need a **secure context** (https or localhost):

1. **Host it** (easiest, works for friends): push this folder to GitHub Pages / Netlify /
   Vercel. Open once on the phone (downloads app + 33 MB basemap + bundle), *Add to Home
   screen* — fully offline from then on. New GPX loads from phone storage need no network.
2. **On-device server**: Termux + `python -m http.server` in this folder on the phone,
   open `http://localhost:8000`. Zero network ever.

`http://<laptop-ip>:8139` over Wi-Fi renders but Chrome blocks GPS/SW on insecure
origins — fine for a look, not for riding.

## Riding it

1. ☰ → pick track → **START**. Mount phone. It beeps before every turn and junction.
2. Multi-day: load the week's GPX the night before (they persist); pick each day's track.
3. Drag to look around (follow pauses) → ◎ snaps back. Off-track buzz = check the banner.

Privacy: the friends layer publishes name + position to a public ntfy.sh topic named after
your ride code — use an unguessable code, or leave it blank.
