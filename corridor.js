/* Corridor tile math for the shared tile archive (pack format v2).
   Pure logic, no DOM/IDB — loaded by index.html and node-testable
   (tests/corridor.test.mjs). Design:
   Dingo/Docs/plans/2026-08-04-shared-tiles-pack-v2-design.md

   Tiers (defaults, tunable here in one place):
     z12-14  track corridor, ~2 km buffer either side
     z8-11   ride bbox padded ~20 km
     z0-7    the whole coverage area (Australia), a few hundred tiles, once
*/
(function (root) {
  'use strict';

  const AU_BBOX = [112.0, -44.2, 154.5, -9.5]; // minLon,minLat,maxLon,maxLat

  const DEFAULTS = {
    corridorKm: 2,
    corridorZooms: [12, 14],
    bboxPadKm: 20,
    bboxZooms: [8, 11],
    coreZooms: [0, 7],
    coreBbox: AU_BBOX,
  };

  function lonLatToTileF(lon, lat, z) {
    const n = 2 ** z;
    const clampedLat = Math.max(Math.min(lat, 85.05), -85.05);
    const x = ((lon + 180) / 360) * n;
    const y =
      ((1 -
        Math.asinh(Math.tan((clampedLat * Math.PI) / 180)) / Math.PI) /
        2) *
      n;
    return [x, y];
  }

  function lonLatToTile(lon, lat, z) {
    const [xf, yf] = lonLatToTileF(lon, lat, z);
    const n = 2 ** z;
    return [
      Math.min(Math.max(Math.floor(xf), 0), n - 1),
      Math.min(Math.max(Math.floor(yf), 0), n - 1),
    ];
  }

  /* km -> tile units at a latitude/zoom (x axis; good enough for y too at
     riding latitudes — the generous buffer absorbs the distortion) */
  function kmToTiles(km, lat, z) {
    const kmPerTileX =
      (40075 * Math.cos((lat * Math.PI) / 180)) / 2 ** z;
    return km / kmPerTileX;
  }

  function addBboxTiles(set, bbox, zmin, zmax) {
    const [minLon, minLat, maxLon, maxLat] = bbox;
    for (let z = zmin; z <= zmax; z++) {
      const [x0, y0] = lonLatToTile(minLon, maxLat, z); // y grows southward
      const [x1, y1] = lonLatToTile(maxLon, minLat, z);
      for (let x = x0; x <= x1; x++)
        for (let y = y0; y <= y1; y++) set.add(z + '/' + x + '/' + y);
    }
  }

  /* tracks: array of point-arrays; each point is {lat, lon} or [lat, lon] */
  function pt(p) {
    return Array.isArray(p) ? { lat: p[0], lon: p[1] } : p;
  }

  function trackBbox(tracks, padKm) {
    let minLon = Infinity, minLat = Infinity, maxLon = -Infinity, maxLat = -Infinity;
    for (const track of tracks)
      for (const raw of track) {
        const p = pt(raw);
        if (!isFinite(p.lat) || !isFinite(p.lon)) continue;
        minLon = Math.min(minLon, p.lon); maxLon = Math.max(maxLon, p.lon);
        minLat = Math.min(minLat, p.lat); maxLat = Math.max(maxLat, p.lat);
      }
    if (!isFinite(minLon)) return null;
    const midLat = (minLat + maxLat) / 2;
    const dLat = padKm / 110.54;
    const dLon = padKm / (111.32 * Math.cos((midLat * Math.PI) / 180));
    return [minLon - dLon, minLat - dLat, maxLon + dLon, maxLat + dLat];
  }

  function addCorridorTiles(set, tracks, bufferKm, zmin, zmax) {
    for (let z = zmin; z <= zmax; z++) {
      const n = 2 ** z;
      for (const track of tracks) {
        let prev = null;
        for (const raw of track) {
          const p = pt(raw);
          if (!isFinite(p.lat) || !isFinite(p.lon)) continue;
          const r = kmToTiles(bufferKm, p.lat, z);
          const [xf, yf] = lonLatToTileF(p.lon, p.lat, z);
          // walk from the previous sample so sparse GPX points can't skip tiles
          let steps = 1;
          if (prev) {
            const d = Math.max(Math.abs(xf - prev[0]), Math.abs(yf - prev[1]));
            steps = Math.max(1, Math.ceil(d / 0.5)); // ~half-tile steps
          }
          for (let s = 1; s <= steps; s++) {
            const fx = prev ? prev[0] + ((xf - prev[0]) * s) / steps : xf;
            const fy = prev ? prev[1] + ((yf - prev[1]) * s) / steps : yf;
            const x0 = Math.max(0, Math.floor(fx - r));
            const x1 = Math.min(n - 1, Math.floor(fx + r));
            const y0 = Math.max(0, Math.floor(fy - r));
            const y1 = Math.min(n - 1, Math.floor(fy + r));
            for (let x = x0; x <= x1; x++)
              for (let y = y0; y <= y1; y++) set.add(z + '/' + x + '/' + y);
          }
          prev = [xf, yf];
        }
      }
    }
  }

  /* The full tile list for a pack's tracks. Returns [{z,x,y}] sorted by zoom
     (low zooms first — the map is usable soonest that way). maxzoom caps the
     result per source (hillshade stops at 12). */
  /* Pass coreZooms: null / bboxZooms: null to skip a tier (aerial uses
     corridor-only — imagery is too heavy for area tiers). */
  function corridorTiles(tracks, opts) {
    const o = Object.assign({}, DEFAULTS, opts || {});
    const set = new Set();
    if (o.coreZooms) addBboxTiles(set, o.coreBbox, o.coreZooms[0], o.coreZooms[1]);
    const bbox = trackBbox(tracks, o.bboxPadKm);
    if (bbox) {
      if (o.bboxZooms) addBboxTiles(set, bbox, o.bboxZooms[0], o.bboxZooms[1]);
      addCorridorTiles(set, tracks, o.corridorKm, o.corridorZooms[0], o.corridorZooms[1]);
    }
    const out = [];
    for (const key of set) {
      const [z, x, y] = key.split('/').map(Number);
      if (o.maxzoom !== undefined && z > o.maxzoom) continue;
      out.push({ z, x, y });
    }
    out.sort((a, b) => a.z - b.z || a.x - b.x || a.y - b.y);
    return out;
  }

  const api = { corridorTiles, trackBbox, lonLatToTile, lonLatToTileF, kmToTiles, DEFAULTS, AU_BBOX };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.DingoCorridor = api;
})(typeof self !== 'undefined' ? self : globalThis);
