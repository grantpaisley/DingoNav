#!/usr/bin/env python3
"""extract-bundle.py — bake a .dingonav bundle into mock-up scene data.

Reads an unzipped .dingonav bundle (bundle.json + basemap.pmtiles + hillshade.pmtiles
+ satellite/z/x/y.jpg) and emits:
  palm-data.js   — const PALM = {...}: tracks, heat, basemap vectors, labels (scene units)
  palm-sat.jpg   — satellite composite for the scene rect (z15, parent fallback)
  palm-hill.png  — hillshade composite (inlined into palm-data.js as data URI)

Scene units: 1 unit = 2 ground metres (Web-Mercator scaled by cos(lat0)), y flipped.
Usage: extract.py <bundle-dir> <out-dir>
"""
import sys, os, io, re, json, math, base64, collections

# ---- Minimal PMTiles v3 + MVT reader (stdlib only) ----
import gzip, io, json, math, struct

def _varints(buf):
    out, shift, val = [], 0, 0
    for b in buf:
        val |= (b & 0x7f) << shift
        if b & 0x80:
            shift += 7
        else:
            out.append(val); shift = 0; val = 0
    return out

def read_varint(data, i):
    shift = val = 0
    while True:
        b = data[i]; i += 1
        val |= (b & 0x7f) << shift
        if not b & 0x80:
            return val, i
        shift += 7

def zigzag(v):
    return (v >> 1) ^ -(v & 1)

class PMTiles:
    def __init__(self, path):
        self.f = open(path, 'rb')
        h = self.f.read(127)
        assert h[:7] == b'PMTiles' and h[7] == 3, 'not pmtiles v3'
        (self.root_off, self.root_len, self.meta_off, self.meta_len,
         self.leaf_off, self.leaf_len, self.data_off, self.data_len) = struct.unpack('<8Q', h[8:72])
        self.internal_comp = h[97]
        self.tile_comp = h[98]
        self.tile_type = h[99]
        self.minz, self.maxz = h[100], h[101]

    def _decomp(self, blob, comp):
        return gzip.decompress(blob) if comp == 2 else blob

    def _read(self, off, ln):
        self.f.seek(off); return self.f.read(ln)

    def _dir(self, off, ln):
        data = self._decomp(self._read(off, ln), self.internal_comp)
        n, i = read_varint(data, 0)
        ids, runs, lens, offs = [], [], [], []
        last = 0
        for _ in range(n):
            v, i = read_varint(data, i); last += v; ids.append(last)
        for _ in range(n):
            v, i = read_varint(data, i); runs.append(v)
        for _ in range(n):
            v, i = read_varint(data, i); lens.append(v)
        for k in range(n):
            v, i = read_varint(data, i)
            if v == 0:
                offs.append(offs[k-1] + lens[k-1])
            else:
                offs.append(v - 1)
        return list(zip(ids, runs, offs, lens))

    def tile_id(self, z, x, y):
        acc = sum(1 << (2*i) for i in range(z))
        # hilbert
        rx = ry = 0; d = 0; s = (1 << z) >> 1
        tx, ty = x, y
        while s > 0:
            rx = 1 if (tx & s) else 0
            ry = 1 if (ty & s) else 0
            d += s * s * ((3 * rx) ^ ry)
            # rotate
            if ry == 0:
                if rx == 1:
                    tx = s - 1 - tx; ty = s - 1 - ty
                tx, ty = ty, tx
            s >>= 1
        return acc + d

    def get(self, z, x, y):
        tid = self.tile_id(z, x, y)
        entries = self._dir(self.root_off, self.root_len)
        for _ in range(4):
            lo, hi, found = 0, len(entries) - 1, None
            while lo <= hi:
                mid = (lo + hi) // 2
                eid, run, off, ln = entries[mid]
                if eid <= tid:
                    found = entries[mid]; lo = mid + 1
                else:
                    hi = mid - 1
            if not found:
                return None
            eid, run, off, ln = found
            if run > 0:
                if tid - eid < run:
                    return self._decomp(self._read(self.data_off + off, ln), self.tile_comp)
                return None
            entries = self._dir(self.leaf_off + off, ln)
        return None

def decode_mvt(blob):
    """returns {layer: {'extent': n, 'features': [{'type':t,'props':{},'geom':[[(x,y)...]...]}]}}"""
    layers = {}
    i = 0
    while i < len(blob):
        key, i = read_varint(blob, i)
        f, w = key >> 3, key & 7
        if f == 3 and w == 2:
            ln, i = read_varint(blob, i)
            name, feats = _decode_layer(blob[i:i+ln])
            layers[name] = feats
            i += ln
        else:
            i = _skip(blob, i, w)
    return layers

def _skip(blob, i, w):
    if w == 0:
        _, i = read_varint(blob, i)
    elif w == 2:
        ln, i = read_varint(blob, i); i += ln
    elif w == 5:
        i += 4
    elif w == 1:
        i += 8
    return i

def _decode_layer(data):
    name, keys, values, raw_feats, extent = '', [], [], [], 4096
    i = 0
    while i < len(data):
        key, i = read_varint(data, i)
        f, w = key >> 3, key & 7
        if f == 1 and w == 2:
            ln, i = read_varint(data, i); name = data[i:i+ln].decode(); i += ln
        elif f == 2 and w == 2:
            ln, i = read_varint(data, i); raw_feats.append(data[i:i+ln]); i += ln
        elif f == 3 and w == 2:
            ln, i = read_varint(data, i); keys.append(data[i:i+ln].decode()); i += ln
        elif f == 4 and w == 2:
            ln, i = read_varint(data, i); values.append(_decode_value(data[i:i+ln])); i += ln
        elif f == 5 and w == 0:
            extent, i = read_varint(data, i)
        else:
            i = _skip(data, i, w)
    feats = []
    for fd in raw_feats:
        feats.append(_decode_feature(fd, keys, values))
    return name, {'extent': extent, 'features': feats}

def _decode_value(data):
    i = 0
    key, i = read_varint(data, i)
    f, w = key >> 3, key & 7
    if f == 1:
        ln, i = read_varint(data, i); return data[i:i+ln].decode()
    if f == 2:
        return struct.unpack('<f', data[i:i+4])[0]
    if f == 3:
        return struct.unpack('<d', data[i:i+8])[0]
    if f in (4, 5):
        v, i = read_varint(data, i); return v
    if f == 6:
        v, i = read_varint(data, i); return zigzag(v)
    if f == 7:
        v, i = read_varint(data, i); return bool(v)
    return None

def _decode_feature(data, keys, values):
    tags, gtype, geom_data = [], 0, b''
    i = 0
    while i < len(data):
        key, i = read_varint(data, i)
        f, w = key >> 3, key & 7
        if f == 2 and w == 2:
            ln, i = read_varint(data, i)
            j = i
            while j < i + ln:
                v, j = read_varint(data, j); tags.append(v)
            i += ln
        elif f == 3 and w == 0:
            gtype, i = read_varint(data, i)
        elif f == 4 and w == 2:
            ln, i = read_varint(data, i); geom_data = data[i:i+ln]; i += ln
        else:
            i = _skip(data, i, w)
    props = {keys[tags[k]]: values[tags[k+1]] for k in range(0, len(tags), 2)}
    # geometry
    rings, ring = [], []
    x = y = 0
    i = 0
    while i < len(geom_data):
        cmd, i = read_varint(geom_data, i)
        op, cnt = cmd & 7, cmd >> 3
        if op == 1:  # MoveTo
            for _ in range(cnt):
                dx, i = read_varint(geom_data, i); dy, i = read_varint(geom_data, i)
                x += zigzag(dx); y += zigzag(dy)
                if ring:
                    rings.append(ring)
                ring = [(x, y)]
        elif op == 2:  # LineTo
            for _ in range(cnt):
                dx, i = read_varint(geom_data, i); dy, i = read_varint(geom_data, i)
                x += zigzag(dx); y += zigzag(dy)
                ring.append((x, y))
        elif op == 7:  # ClosePath
            if ring:
                ring.append(ring[0])
    if ring:
        rings.append(ring)
    return {'type': gtype, 'props': props, 'geom': rings}


# ---- end reader ----
from PIL import Image

M_PER_UNIT = 2.0
PAD_M = 500.0
R = 6378137.0

bundle_dir, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)
bundle = json.load(open(os.path.join(bundle_dir, 'bundle.json')))

# ---------------- projection ----------------
def merc(lon, lat):
    return R * math.radians(lon), R * math.asinh(math.tan(math.radians(lat)))

def parse_gpx(gpx):
    pts = []
    for m in re.finditer(r'<trkpt lat="([\-\d.]+)" lon="([\-\d.]+)"\s*>(.*?)</trkpt>', gpx, re.S):
        lat, lon = float(m.group(1)), float(m.group(2))
        em = re.search(r'<ele>([\-\d.]+)</ele>', m.group(3))
        pts.append((lon, lat, float(em.group(1)) if em else None))
    if not pts:  # self-closing or attr order variants
        for m in re.finditer(r'<trkpt[^>]*lat="([\-\d.]+)"[^>]*lon="([\-\d.]+)"', gpx):
            pts.append((float(m.group(1)), float(m.group(2)), None))
    return pts

tracks = [parse_gpx(t['gpx']) for t in bundle['tracks']]
allpts = [p for t in tracks for p in t]
lat0 = sum(p[1] for p in allpts) / len(allpts)
COS = math.cos(math.radians(lat0))
K = COS / M_PER_UNIT   # merc metres -> scene units

mxs, mys = zip(*[merc(p[0], p[1]) for p in allpts])
pad = PAD_M / COS
minx, maxx, miny, maxy = min(mxs) - pad, max(mxs) + pad, min(mys) - pad, max(mys) + pad
SW, SH = (maxx - minx) * K, (maxy - miny) * K

def scene(lon, lat):
    mx, my = merc(lon, lat)
    return (mx - minx) * K, (maxy - my) * K

print(f'scene {SW:.0f} x {SH:.0f} units ({SW*M_PER_UNIT/1000:.1f} x {SH*M_PER_UNIT/1000:.1f} km), lat0 {lat0:.4f}')

# ---------------- geometry helpers ----------------
def simplify(pts, tol):
    """Douglas-Peucker, iterative."""
    if len(pts) < 3:
        return pts[:]
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    t2 = tol * tol
    while stack:
        a, b = stack.pop()
        ax, ay = pts[a][0], pts[a][1]
        bx, by = pts[b][0], pts[b][1]
        dx, dy = bx - ax, by - ay
        dd = dx * dx + dy * dy
        worst, wi = -1.0, -1
        for i in range(a + 1, b):
            px, py = pts[i][0] - ax, pts[i][1] - ay
            if dd:
                t = max(0.0, min(1.0, (px * dx + py * dy) / dd))
                ex, ey = px - t * dx, py - t * dy
            else:
                ex, ey = px, py
            e = ex * ex + ey * ey
            if e > worst:
                worst, wi = e, i
        if worst > t2:
            keep[wi] = True
            stack.append((a, wi)); stack.append((wi, b))
    return [p for p, k in zip(pts, keep) if k]

def rnd(v):
    s = f'{v:.1f}'
    return s[:-2] if s.endswith('.0') else s

def path_d(lines, close=False):
    """relative-lineto path string for a list of polylines"""
    out = []
    for pts in lines:
        if len(pts) < 2:
            continue
        x0, y0 = pts[0][0], pts[0][1]
        seg = [f'M{rnd(x0)} {rnd(y0)}']
        cx, cy = x0, y0
        for p in pts[1:]:
            dx, dy = p[0] - cx, p[1] - cy
            seg.append(f'l{rnd(dx)} {rnd(dy)}')
            cx += float(rnd(dx)); cy += float(rnd(dy))
        if close:
            seg.append('Z')
        out.append(''.join(seg))
    return ''.join(out)

def clip_line(pts, x0, y0, x1, y1):
    """keep sub-runs inside rect (segment-level, no exact intersection — fine at tile seams)"""
    runs, cur = [], []
    for p in pts:
        if x0 <= p[0] <= x1 and y0 <= p[1] <= y1:
            cur.append(p)
        else:
            if len(cur) > 1:
                runs.append(cur)
            cur = [p] if False else []
    if len(cur) > 1:
        runs.append(cur)
    return runs

def poly_area(pts):
    a = 0.0
    for i in range(len(pts) - 1):
        a += pts[i][0] * pts[i+1][1] - pts[i+1][0] * pts[i][1]
    return abs(a) / 2

# ---------------- tracks -> route/track2 ----------------
def to_scene(track):
    out = []
    for lon, lat, ele in track:
        x, y = scene(lon, lat)
        out.append((x, y, ele))
    return out

route_full = to_scene(tracks[0])
route = simplify(route_full, 0.6)
track2 = simplify(to_scene(tracks[1]), 0.8) if len(tracks) > 1 else []
print(f'route pts {len(route_full)} -> {len(route)}; track2 -> {len(track2)}')

# cumulative length of the simplified route (this is what the SVG measures too)
cum = [0.0]
for i in range(1, len(route)):
    cum.append(cum[-1] + math.hypot(route[i][0]-route[i-1][0], route[i][1]-route[i-1][1]))
LEN = cum[-1]
print(f'route length {LEN*M_PER_UNIT/1000:.1f} km ({LEN:.0f} units)')

# ---------------- basemap vectors ----------------
pm = PMTiles(os.path.join(bundle_dir, 'basemap.pmtiles'))
BZ = pm.maxz
def t2m(z, xt, yt):
    n = 2 ** z
    lon = xt / n * 360 - 180
    my = R * math.pi * (1 - 2 * yt / n)
    mx = R * math.radians(lon)
    return mx, my

def tile_range(z):
    n = 2 ** z
    def t(mx, my):
        lon = math.degrees(mx / R)
        xt = (lon + 180) / 360 * n
        yt = n * (1 - my / (R * math.pi)) / 2
        return xt, yt
    x0, y1 = t(minx, miny); x1, y0 = t(maxx, maxy)
    return int(x0), int(x1), int(y0), int(y1)

ROAD_GROUP = {  # (kind, kind_detail) -> group
    'highway': 'hwy', 'major_road': 'major', 'minor_road': 'minor', 'rail': 'rail',
}
groups = collections.defaultdict(list)   # lines per group, scene coords
polys = collections.defaultdict(list)
road_segs = []                            # (x1,y1,x2,y2, surf) for route classification
name_lines = collections.defaultdict(list)  # label name -> polylines

X0, X1, Y0, Y1 = tile_range(BZ)
for xt in range(X0, X1 + 1):
    for yt in range(Y0, Y1 + 1):
        blob = pm.get(BZ, xt, yt)
        if not blob:
            continue
        layers = decode_mvt(blob)
        # tile rect in scene coords
        tx0, ty0 = t2m(BZ, xt, yt)
        tx1, ty1 = t2m(BZ, xt + 1, yt + 1)
        ext = 4096
        def tf(px, py):
            mx = tx0 + (tx1 - tx0) * px / ext
            my = ty0 + (ty1 - ty0) * py / ext
            return (mx - minx) * K, (maxy - my) * K
        rx0, ry0 = tf(0, 0); rx1, ry1 = tf(ext, ext)
        for lname, want_poly in (('roads', False), ('water', None), ('landuse', True), ('buildings', True)):
            layer = layers.get(lname)
            if not layer:
                continue
            ext = layer['extent']
            for f in layer['features']:
                p = f['props']
                kind, det = p.get('kind'), p.get('kind_detail')
                geo = [[tf(px, py) for px, py in ring] for ring in f['geom']]
                if lname == 'roads':
                    if kind == 'path':
                        g = 'track' if det == 'track' else 'path'
                    else:
                        g = ROAD_GROUP.get(kind)
                    if not g:
                        continue
                    surf = ('dirt' if g == 'track' else 'single' if g == 'path'
                            else None if g == 'rail' else 'sealed')
                    for ring in geo:
                        for run in clip_line(ring, rx0, ry0, rx1, ry1):
                            rs = simplify(run, 0.5)
                            groups[g].append(rs)
                            if surf:
                                for i in range(len(rs) - 1):
                                    road_segs.append((rs[i][0], rs[i][1], rs[i+1][0], rs[i+1][1], surf))
                            if p.get('name') and g in ('hwy', 'major', 'minor', 'track'):
                                name_lines[p['name']].append(rs)
                elif lname == 'water':
                    if f['type'] == 3 and kind in ('water', 'swimming_pool', 'basin'):
                        for ring in geo:
                            r = simplify(ring, 0.8)
                            if poly_area(r) > 40:
                                polys['water'].append(r)
                        if p.get('name'):
                            name_lines['~water~' + p['name']].append(geo[0])
                    elif f['type'] == 2 and kind in ('stream', 'river', 'ditch', 'drain', 'canal'):
                        for ring in geo:
                            for run in clip_line(ring, rx0, ry0, rx1, ry1):
                                groups['creek' if kind == 'stream' else 'river'].append(simplify(run, 0.8))
                                if p.get('name') and kind in ('river', 'stream'):
                                    name_lines['~creek~' + p['name']].append(simplify(run, 2))
                elif lname == 'landuse' and f['type'] == 3:
                    cls = ('bush' if kind in ('wood', 'forest', 'nature_reserve', 'scrub', 'wetland')
                           else 'park' if kind in ('grass', 'meadow', 'garden', 'park', 'recreation_ground',
                                                   'pitch', 'playground', 'village_green', 'cemetery')
                           else 'urban' if kind in ('residential', 'industrial', 'commercial', 'retail')
                           else 'clear' if kind in ('farmland', 'farmyard', 'orchard', 'quarry', 'brownfield')
                           else None)
                    if not cls:
                        continue
                    for ring in geo:
                        r = simplify(ring, 1.2)
                        if poly_area(r) > 150:
                            polys[cls].append(r)
                elif lname == 'buildings' and f['type'] == 3 and kind == 'building':
                    for ring in geo:
                        r = simplify(ring, 0.5)
                        if poly_area(r) > 6:
                            polys['bldg'].append(r)

print('vector groups:', {g: len(v) for g, v in groups.items()})
print('poly groups:', {g: len(v) for g, v in polys.items()})

# labels: pois places (administrative/locality) + a few longest named ways
pois_labels = []
for xt in range(X0, X1 + 1):
    for yt in range(Y0, Y1 + 1):
        blob = pm.get(BZ, xt, yt)
        if not blob:
            continue
        layers = decode_mvt(blob)
        tx0, ty0 = t2m(BZ, xt, yt)
        tx1, ty1 = t2m(BZ, xt + 1, yt + 1)
        for lname in ('places', 'pois'):
            layer = layers.get(lname)
            if not layer:
                continue
            ext = layer['extent']
            for f in layer['features']:
                p = f['props']
                if not p.get('name'):
                    continue
                if lname == 'pois' and p.get('kind') not in ('administrative', 'forest', 'peak'):
                    continue
                px, py = f['geom'][0][0]
                if not (0 <= px <= ext and 0 <= py <= ext):
                    continue
                mx = tx0 + (tx1 - tx0) * px / ext
                my = ty0 + (ty1 - ty0) * py / ext
                x, y = (mx - minx) * K, (maxy - my) * K
                if 0 <= x <= SW and 0 <= y <= SH:
                    pois_labels.append({'t': p['name'], 'x': round(x, 1), 'y': round(y, 1),
                                        'k': 'town' if p.get('kind') in ('administrative',) or lname == 'places'
                                             else p.get('kind')})
# dedupe by name
seen = set(); pt_labels = []
for l in pois_labels:
    if l['t'] in seen:
        continue
    seen.add(l['t']); pt_labels.append(l)

def longest_run(name):
    """stitch runs for a named way, return the single longest polyline"""
    runs = [r for r in name_lines.get(name, []) if len(r) > 1]
    # greedy stitch by endpoints
    changed = True
    while changed and len(runs) > 1:
        changed = False
        for i in range(len(runs)):
            for j in range(i + 1, len(runs)):
                a, b = runs[i], runs[j]
                def d(p, q): return math.hypot(p[0]-q[0], p[1]-q[1])
                if d(a[-1], b[0]) < 3: runs[i] = a + b[1:]
                elif d(b[-1], a[0]) < 3: runs[i] = b + a[1:]
                elif d(a[-1], b[-1]) < 3: runs[i] = a + b[::-1][1:]
                elif d(a[0], b[0]) < 3: runs[i] = a[::-1] + b[1:]
                else: continue
                runs.pop(j); changed = True
                break
            if changed:
                break
    best = max(runs, key=lambda r: sum(math.hypot(r[k+1][0]-r[k][0], r[k+1][1]-r[k][1]) for k in range(len(r)-1)), default=None)
    return best

way_labels = []
lengths = {}
for name in name_lines:
    tot = sum(sum(math.hypot(r[k+1][0]-r[k][0], r[k+1][1]-r[k][1]) for k in range(len(r)-1)) for r in name_lines[name])
    lengths[name] = tot
wanted = sorted((n for n in lengths if not n.startswith('~')), key=lambda n: -lengths[n])[:6]
wanted += [n for n in lengths if n.startswith('~creek~')][:0]
creeks = sorted((n for n in lengths if n.startswith('~creek~')), key=lambda n: -lengths[n])[:2]
for name in wanted + creeks:
    run = longest_run(name)
    if not run or len(run) < 2:
        continue
    L = sum(math.hypot(run[k+1][0]-run[k][0], run[k+1][1]-run[k][1]) for k in range(len(run)-1))
    if L < 120:
        continue
    # left-to-right for readable text
    if run[0][0] > run[-1][0]:
        run = run[::-1]
    way_labels.append({'t': name.replace('~creek~', ''), 'd': path_d([simplify(run, 3)]),
                       'k': 'water' if name.startswith('~creek~') else 'road'})
print('labels:', [l['t'] for l in pt_labels], '| ways:', [l['t'] for l in way_labels])

# ---------------- route surface classification ----------------
GRID = 40.0
grid = collections.defaultdict(list)
for seg in road_segs:
    x1, y1, x2, y2, surf = seg
    for gx in range(int(min(x1, x2) // GRID), int(max(x1, x2) // GRID) + 1):
        for gy in range(int(min(y1, y2) // GRID), int(max(y1, y2) // GRID) + 1):
            grid[(gx, gy)].append(seg)

def nearest_surf(x, y, rmax=15.0):
    best, bs = rmax * rmax, None
    gx, gy = int(x // GRID), int(y // GRID)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for (x1, y1, x2, y2, surf) in grid.get((gx + dx, gy + dy), ()):
                ddx, ddy = x2 - x1, y2 - y1
                dd = ddx * ddx + ddy * ddy
                t = 0 if not dd else max(0.0, min(1.0, ((x - x1) * ddx + (y - y1) * ddy) / dd))
                ex, ey = x - x1 - t * ddx, y - y1 - t * ddy
                e = ex * ex + ey * ey
                if e < best:
                    best, bs = e, surf
    return bs or 'unmapped'

surfs = [nearest_surf(p[0], p[1]) for p in route]
# majority smoothing over ±4 samples, then enforce min span 25 units
sm = []
for i in range(len(surfs)):
    w = surfs[max(0, i-4):i+5]
    sm.append(collections.Counter(w).most_common(1)[0][0])
spans = []  # (surf, i0, i1)
for i, s in enumerate(sm):
    if spans and spans[-1][0] == s:
        spans[-1][2] = i
    else:
        spans.append([s, i, i])
# merge short spans into previous
merged = []
for s, i0, i1 in spans:
    if merged and cum[i1] - cum[i0] < 40:
        merged[-1][2] = i1
    else:
        merged.append([s, i0, i1])
# re-merge adjacent same-surf
spans = []
for s, i0, i1 in merged:
    if spans and spans[-1][0] == s:
        spans[-1][2] = i1
    else:
        spans.append([s, i0, i1])
surf_dist = collections.Counter()
for s, i0, i1 in spans:
    surf_dist[s] += (cum[i1] - cum[i0]) * M_PER_UNIT / 1000
print('surface spans:', len(spans), {k: f'{v:.1f}km' for k, v in surf_dist.items()})

span_out = [{'s': s, 'f0': round(cum[i0] / LEN, 4), 'f1': round(cum[i1] / LEN, 4),
             'd': path_d([route[i0:i1 + 1]])} for s, i0, i1 in spans]

# ---------------- grades (real elevation) ----------------
N = 600
grades = []
eles = [p[2] for p in route]
# fill None ele by neighbours
for i in range(len(eles)):
    if eles[i] is None:
        eles[i] = eles[i - 1] if i else 0
half = 75.0 / M_PER_UNIT  # ±75 m window
j0 = j1 = 0
for k in range(N):
    d = LEN * k / (N - 1)
    while j0 < len(cum) - 1 and cum[j0] < d - half: j0 += 1
    while j1 < len(cum) - 1 and cum[j1] < d + half: j1 += 1
    dd = (cum[j1] - cum[j0]) * M_PER_UNIT
    de = (eles[j1] - eles[j0]) if dd else 0
    grades.append(round(abs(de / dd * 100), 1) if dd > 10 else 0.0)
print(f'grade max {max(grades)}%, mean {sum(grades)/len(grades):.1f}%')

# ---------------- cues (real turns) ----------------
def heading(i):
    a, b = route[max(0, i - 2)], route[min(len(route) - 1, i + 2)]
    return math.atan2(b[1] - a[1], b[0] - a[0])

turns = []
for i in range(3, len(route) - 3):
    da = heading(i + 2) - heading(i - 2)
    while da > math.pi: da -= 2 * math.pi
    while da < -math.pi: da += 2 * math.pi
    turns.append((abs(da), da, i))
turns.sort(reverse=True)
cues, used = [], []
for mag, da, i in turns:
    if mag < math.radians(70):
        break
    if any(abs(cum[i] - cum[j]) < 400 for j in used):
        continue
    used.append(i)
    cues.append({'f': round(cum[i] / LEN, 4), 'icon': '↰' if da < 0 else '↱',
                 'label': ('Hairpin ' if mag > math.radians(130) else 'Turn ') + ('left' if da < 0 else 'right')})
    if len(cues) >= 6:
        break
cues.sort(key=lambda c: c['f'])
hairpin = max(cues, key=lambda c: 'Hairpin' in c['label'], default=cues[0] if cues else None)
print('cues:', [(c['f'], c['label']) for c in cues])

# ---------------- heat ----------------
# one path PER FEATURE (per ride): overlap between rides accumulates opacity like the
# real additive heat renderer; keeps the DOM at ~70 paths instead of ~8000
heat = {'own': [], 'plan': [], 'other': []}
hpts_in = hpts_out = 0
for f in bundle['heatmap']['features']:
    cls = f['properties'].get('class', 'own')
    g = f['geometry']
    lines = g['coordinates'] if g['type'] == 'MultiLineString' else [g['coordinates']]
    runs = []
    for ls in lines:
        pts = [scene(x, y) for x, y in ls]
        hpts_in += len(pts)
        for run in clip_line(pts, -100, -100, SW + 100, SH + 100):
            s = simplify(run, 2.0)
            if len(s) > 2 or (len(s) == 2 and math.hypot(s[1][0]-s[0][0], s[1][1]-s[0][1]) > 6):
                hpts_out += len(s)
                runs.append(s)
    if runs:
        heat.setdefault(cls, []).append(path_d(runs))
print(f'heat pts {hpts_in} -> {hpts_out}; feature paths', {k: len(v) for k, v in heat.items()})

# ---------------- satellite composite ----------------
SZ = 15
sx0, sx1, sy0, sy1 = tile_range(SZ)
TILE = 256
img = Image.new('RGB', ((sx1 - sx0 + 1) * TILE, (sy1 - sy0 + 1) * TILE), (60, 70, 55))
def sat_tile(z, x, y):
    p = os.path.join(bundle_dir, 'satellite', str(z), str(x), f'{y}.jpg')
    if os.path.exists(p):
        return Image.open(p).convert('RGB')
    if z > 10:  # parent fallback, upscaled
        parent = sat_tile(z - 1, x // 2, y // 2)
        if parent:
            q = parent.crop(((x % 2) * 128, (y % 2) * 128, (x % 2) * 128 + 128, (y % 2) * 128 + 128))
            return q.resize((TILE, TILE), Image.BILINEAR)
    return None
missing = 0
for x in range(sx0, sx1 + 1):
    for y in range(sy0, sy1 + 1):
        t = sat_tile(SZ, x, y)
        if t:
            img.paste(t, ((x - sx0) * TILE, (y - sy0) * TILE))
        else:
            missing += 1
# crop to scene rect: scene(0,0) is (minx, maxy)
def merc_to_satpx(mx, my):
    n = 2 ** SZ
    lon = math.degrees(mx / R)
    xt = (lon + 180) / 360 * n
    yt = n * (1 - my / (R * math.pi)) / 2
    return (xt - sx0) * TILE, (yt - sy0) * TILE
cx0, cy0 = merc_to_satpx(minx, maxy)
cx1, cy1 = merc_to_satpx(maxx, miny)
img = img.crop((int(cx0), int(cy0), int(cx1), int(cy1)))
img.save(os.path.join(out_dir, 'palm-sat.jpg'), quality=68, optimize=True)
print(f'satellite {img.size} missing z{SZ} tiles filled from parents: {missing}; '
      f'{os.path.getsize(os.path.join(out_dir, "palm-sat.jpg"))//1024} KB')

# ---------------- hillshade (inline data URI) ----------------
# the bundle's "hillshade" pmtiles is terrarium-encoded DEM (ele = R*256+G+B/256-32768);
# the app shades it client-side, so shade it here: Lambertian, NW light, 128 = flat
# (neutral under soft-light blending)
hill_uri = None
try:
    hs = PMTiles(os.path.join(bundle_dir, 'hillshade.pmtiles'))
    HZ = hs.maxz
    hx0, hx1, hy0, hy1 = tile_range(HZ)
    dem_im = Image.new('RGB', ((hx1 - hx0 + 1) * TILE, (hy1 - hy0 + 1) * TILE), (128, 0, 0))
    got = 0
    for x in range(hx0, hx1 + 1):
        for y in range(hy0, hy1 + 1):
            blob = hs.get(HZ, x, y)
            if blob:
                dem_im.paste(Image.open(io.BytesIO(blob)).convert('RGB'), ((x - hx0) * TILE, (y - hy0) * TILE))
                got += 1
    def merc_to_hpx(mx, my):
        n = 2 ** HZ
        lon = math.degrees(mx / R)
        xt = (lon + 180) / 360 * n
        yt = n * (1 - my / (R * math.pi)) / 2
        return (xt - hx0) * TILE, (yt - hy0) * TILE
    hx, hy = merc_to_hpx(minx, maxy)
    hx2, hy2 = merc_to_hpx(maxx, miny)
    P = 2  # padding px so the gradient kernel has neighbours at the crop edge
    cw, ch = int(hx2) - int(hx), int(hy2) - int(hy)
    dem_crop = dem_im.crop((int(hx) - P, int(hy) - P, int(hx2) + P, int(hy2) + P))
    w, h = dem_crop.size
    px = dem_crop.load()
    ele = [[px[i, j][0] * 256 + px[i, j][1] + px[i, j][2] / 256 - 32768
            for i in range(w)] for j in range(h)]
    # metres per DEM pixel at this latitude
    n = 2 ** HZ
    mpp = math.cos(math.radians(lat0)) * 2 * math.pi * R / (n * TILE)
    az, alt = math.radians(315), math.radians(45)
    flat = math.sin(alt)
    out = Image.new('L', (cw, ch))
    op = out.load()
    for j in range(ch):
        jj = j + P
        for i in range(cw):
            ii = i + P
            dzdx = (ele[jj][ii + 1] - ele[jj][ii - 1]) / (2 * mpp)
            dzdy = (ele[jj + 1][ii] - ele[jj - 1][ii]) / (2 * mpp)
            slope = math.atan(1.3 * math.hypot(dzdx, dzdy))  # 1.3 = mild exaggeration
            aspect = math.atan2(dzdy, -dzdx)
            I = (math.sin(alt) * math.cos(slope) +
                 math.cos(alt) * math.sin(slope) * math.cos(az - math.pi / 2 - aspect))
            op[i, j] = max(0, min(255, round(128 * max(0.0, I) / flat)))
    out = out.resize((cw * 3, ch * 3), Image.BILINEAR)  # smooth the z12 chunkiness
    out.save(os.path.join(out_dir, 'palm-hill.png'), optimize=True)
    hill_uri = 'palm-hill.png'
    print(f'hillshade DEM {cw}x{ch} tiles {got}, '
          f'{os.path.getsize(os.path.join(out_dir, "palm-hill.png"))//1024} KB')
except Exception as e:
    print('hillshade skipped:', e)

# ---------------- emit ----------------
data = {
    'name': bundle.get('name', 'bundle'),
    'attribution': bundle.get('satellite', {}).get('attribution', ''),
    'W': round(SW, 1), 'H': round(SH, 1), 'mPerUnit': M_PER_UNIT,
    'route': {
        'd': path_d([route]),
        'spans': span_out,
        'grades': grades,
        'cues': cues,
        'idleF': round(max(0.02, (hairpin['f'] if hairpin else 0.3) - 250 / (LEN * M_PER_UNIT) * 1), 4)
                 if cues else 0.3,
        'lenM': round(LEN * M_PER_UNIT),
        'name': bundle['tracks'][0]['name'],
    },
    'track2': {'d': path_d([track2]), 'name': bundle['tracks'][1]['name']} if track2 else None,
    'heat': heat,
    'base': {
        'lines': {g: path_d(v) for g, v in groups.items()},
        'polys': {g: path_d(v, close=True) for g, v in polys.items()},
    },
    'labels': {'points': pt_labels, 'ways': way_labels},
    'sat': 'palm-sat.jpg',
    'hill': hill_uri,
}
# idleF: sit ~500 m before the hairpin so the approach story shows
if cues and hairpin:
    data['route']['idleF'] = round(max(0.02, hairpin['f'] - (500 / M_PER_UNIT) / LEN), 4)

js = 'const PALM = ' + json.dumps(data, separators=(',', ':')) + ';\n'
open(os.path.join(out_dir, 'palm-data.js'), 'w').write(js)
print(f'palm-data.js {len(js)//1024} KB')
