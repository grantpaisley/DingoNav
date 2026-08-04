// node --test tests/
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { corridorTiles, trackBbox, lonLatToTile, kmToTiles, DEFAULTS } =
  require("../corridor.js");

// A short ride near Palm Dale (Central Coast NSW)
const RIDE = [
  [
    { lat: -33.28, lon: 151.32 },
    { lat: -33.29, lon: 151.34 },
    { lat: -33.31, lon: 151.36 },
  ],
];

test("lonLatToTile matches known values", () => {
  // OSM slippy-map reference: Sydney (151.2093, -33.8688) at z10 -> 942/614
  assert.deepEqual(lonLatToTile(151.2093, -33.8688, 10), [942, 614]);
  assert.deepEqual(lonLatToTile(0, 0, 0), [0, 0]);
});

test("kmToTiles scales with zoom", () => {
  const z12 = kmToTiles(2, -33, 12);
  const z14 = kmToTiles(2, -33, 14);
  assert.ok(Math.abs(z14 / z12 - 4) < 1e-9, "two zooms = 4x tile units");
});

test("corridor includes tiles on and near the track at z12-14", () => {
  const tiles = corridorTiles(RIDE);
  const keys = new Set(tiles.map((t) => `${t.z}/${t.x}/${t.y}`));
  for (const p of RIDE[0]) {
    for (let z = 12; z <= 14; z++) {
      const [x, y] = lonLatToTile(p.lon, p.lat, z);
      assert.ok(keys.has(`${z}/${x}/${y}`), `track point tile ${z}/${x}/${y}`);
    }
    // 2 km ≈ a full tile only at z14 — neighbours guaranteed there
    const [x14, y14] = lonLatToTile(p.lon, p.lat, 14);
    assert.ok(keys.has(`14/${x14 + 1}/${y14}`), "buffer neighbour at z14");
  }
});

test("corridor excludes tiles far from the ride at high zoom", () => {
  const tiles = corridorTiles(RIDE);
  const keys = new Set(tiles.map((t) => `${t.z}/${t.x}/${t.y}`));
  // Perth is ~3300 km away — its z14 tile must not be present
  const [x, y] = lonLatToTile(115.86, -31.95, 14);
  assert.ok(!keys.has(`14/${x}/${y}`));
});

test("bbox tier covers the padded ride area at z8-11", () => {
  const tiles = corridorTiles(RIDE);
  const keys = new Set(tiles.map((t) => `${t.z}/${t.x}/${t.y}`));
  const bbox = trackBbox(RIDE, DEFAULTS.bboxPadKm);
  for (let z = 8; z <= 11; z++) {
    const [x0, y0] = lonLatToTile(bbox[0], bbox[3], z);
    const [x1, y1] = lonLatToTile(bbox[2], bbox[1], z);
    assert.ok(keys.has(`${z}/${x0}/${y0}`) && keys.has(`${z}/${x1}/${y1}`),
      `bbox corners at z${z}`);
  }
});

test("core tier is present and small", () => {
  const tiles = corridorTiles(RIDE);
  const core = tiles.filter((t) => t.z <= 7);
  assert.ok(core.length > 50, "covers AU overview");
  assert.ok(core.length < 1500, "stays a few hundred tiles");
});

test("maxzoom caps the list (hillshade)", () => {
  const tiles = corridorTiles(RIDE, { maxzoom: 12 });
  assert.ok(tiles.every((t) => t.z <= 12));
  assert.ok(tiles.some((t) => t.z === 12), "corridor z12 still present");
});

test("sparse points cannot skip corridor tiles", () => {
  // two points ~11 km apart, straight line
  const sparse = [[{ lat: -33.0, lon: 151.0 }, { lat: -33.1, lon: 151.0 }]];
  const tiles = corridorTiles(sparse);
  const keys = new Set(tiles.map((t) => `${t.z}/${t.x}/${t.y}`));
  // midpoint tile at z14 must be filled in by segment walking
  const [x, y] = lonLatToTile(151.0, -33.05, 14);
  assert.ok(keys.has(`14/${x}/${y}`));
});

test("total size is sane for a typical ride", () => {
  const tiles = corridorTiles(RIDE);
  assert.ok(tiles.length > 300 && tiles.length < 20000, `got ${tiles.length}`);
});

test("empty tracks still yield the core tier", () => {
  const tiles = corridorTiles([]);
  assert.ok(tiles.length > 50);
  assert.ok(tiles.every((t) => t.z <= 7));
});
