#!/usr/bin/env python3
"""Build bundle.json for TrailNav: heatmap GeoJSON + GPX tracks pre-loaded on first open.

Usage:
  ./make_bundle.py --heatmap heatmap.geojson track1.gpx track2.gpx ... [-o bundle.json]

Regenerate this each night (or per trip) with the tracks you want, drop it next to
index.html, and the app pre-loads everything on first open (stored in IndexedDB after).
"""
import argparse, json, os, sys

p = argparse.ArgumentParser()
p.add_argument('--heatmap', help='heatmap GeoJSON file (from dingo export)')
p.add_argument('tracks', nargs='*', help='GPX files')
p.add_argument('-o', '--out', default='bundle.json')
a = p.parse_args()

bundle = {}
if a.heatmap:
    bundle['heatmap'] = json.load(open(a.heatmap))
    bundle['heatmapName'] = os.path.basename(a.heatmap)
bundle['tracks'] = []
for t in a.tracks:
    bundle['tracks'].append({'name': os.path.basename(t), 'gpx': open(t, encoding='utf-8').read()})

json.dump(bundle, open(a.out, 'w'), separators=(',', ':'))
sz = os.path.getsize(a.out) / 1e6
print(f'wrote {a.out}: {len(bundle["tracks"])} tracks'
      + (f' + heatmap ({len(bundle["heatmap"]["features"])} features)' if a.heatmap else '')
      + f', {sz:.1f} MB')
