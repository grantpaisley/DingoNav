#!/usr/bin/env python3
"""Cut an offline terrain-shading DEM for DingoNav.

Downloads Terrarium-encoded elevation tiles (AWS Open Data terrain tiles,
free, no key) for a bounding box and packs them into a raster-dem .pmtiles.
DingoNav renders them as a MapLibre hillshade layer under the trails —
flat 2D relief, no live 3D cost beyond the shading pass.

    ./make_hillshade.py --bbox 150.85,-33.75,151.85,-32.85
    ./make_hillshade.py --basemap basemap/central-coast.pmtiles   # reuse its bounds
    ./make_hillshade.py ... -o basemap/hillshade.pmtiles --maxzoom 12

Drop the output at basemap/hillshade.pmtiles for auto-download on first
open (same deal as the basemap), or load any file in-app via ☰.

Needs: pip install pmtiles
"""
import argparse, io, math, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

from pmtiles.tile import Compression, TileType, zxy_to_tileid
from pmtiles.writer import Writer

TILE_URL = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'
ATTRIBUTION = 'Terrain: Mapzen/AWS Open Data (SRTM, Geoscience Australia et al.)'


def lonlat_to_tile(lon, lat, z):
    n = 2 ** z
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return min(max(x, 0), n - 1), min(max(y, 0), n - 1)


def tiles_for_bbox(bbox, zmin, zmax):
    min_lon, min_lat, max_lon, max_lat = bbox
    for z in range(zmin, zmax + 1):
        x0, y0 = lonlat_to_tile(min_lon, max_lat, z)  # y grows southward
        x1, y1 = lonlat_to_tile(max_lon, min_lat, z)
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                yield z, x, y


def fetch(zxy, retries=4):
    z, x, y = zxy
    url = TILE_URL.format(z=z, x=x, y=y)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return zxy, r.read()
        except Exception as e:
            if attempt == retries - 1:
                raise RuntimeError(f'{url}: {e}') from e
            time.sleep(2 ** attempt)


def bounds_from_basemap(path):
    from pmtiles.reader import Reader, MmapSource
    with open(path, 'rb') as f:
        h = Reader(MmapSource(f)).header()
    return [h['min_lon_e7'] / 1e7, h['min_lat_e7'] / 1e7,
            h['max_lon_e7'] / 1e7, h['max_lat_e7'] / 1e7]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--bbox', help='minLon,minLat,maxLon,maxLat')
    ap.add_argument('--basemap', help='existing .pmtiles basemap to copy the bounds from')
    ap.add_argument('--minzoom', type=int, default=6)
    ap.add_argument('--maxzoom', type=int, default=12,
                    help='12 ≈ 38 m/px, plenty for shading (MapLibre overzooms above it)')
    ap.add_argument('-o', '--output', default='basemap/hillshade.pmtiles')
    ap.add_argument('-j', '--jobs', type=int, default=8, help='parallel downloads')
    args = ap.parse_args()

    if args.bbox:
        bbox = [float(v) for v in args.bbox.split(',')]
    elif args.basemap:
        bbox = bounds_from_basemap(args.basemap)
    elif os.path.exists('basemap/central-coast.pmtiles'):
        bbox = bounds_from_basemap('basemap/central-coast.pmtiles')
        print('no --bbox/--basemap given, using basemap/central-coast.pmtiles bounds')
    else:
        ap.error('need --bbox or --basemap')
    if len(bbox) != 4 or bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
        ap.error(f'bad bbox {bbox} (want minLon,minLat,maxLon,maxLat)')

    todo = list(tiles_for_bbox(bbox, args.minzoom, args.maxzoom))
    print(f'bbox {[round(v, 4) for v in bbox]}  z{args.minzoom}-{args.maxzoom}  {len(todo)} tiles')

    tiles, done = {}, 0
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for zxy, data in pool.map(fetch, todo):
            tiles[zxy] = data
            done += 1
            if done % 50 == 0 or done == len(todo):
                print(f'\r  downloaded {done}/{len(todo)}', end='', flush=True)
    print()

    buf = io.BytesIO()
    w = Writer(buf)
    for zxy in sorted(tiles, key=lambda t: zxy_to_tileid(*t)):
        w.write_tile(zxy_to_tileid(*zxy), tiles[zxy])
    w.finalize(
        {'tile_type': TileType.PNG, 'tile_compression': Compression.NONE,
         'min_lon_e7': int(bbox[0] * 1e7), 'min_lat_e7': int(bbox[1] * 1e7),
         'max_lon_e7': int(bbox[2] * 1e7), 'max_lat_e7': int(bbox[3] * 1e7),
         'center_zoom': (args.minzoom + args.maxzoom) // 2},
        {'name': os.path.basename(args.output), 'format': 'png',
         'encoding': 'terrarium', 'attribution': ATTRIBUTION})
    with open(args.output, 'wb') as f:
        f.write(buf.getvalue())
    print(f'{args.output}: {buf.tell() / 1e6:.1f} MB')


if __name__ == '__main__':
    sys.exit(main())
