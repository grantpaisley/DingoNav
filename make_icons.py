#!/usr/bin/env python3
"""Generate TrailNav PWA icons (pure stdlib — no PIL)."""
import struct, zlib, math

def png(w, h, rgba):
    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c))
    raw = b''.join(b'\x00' + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9))
            + chunk(b'IEND', b''))

def make(size, path):
    px = bytearray(size * size * 4)
    bg, orange, cyan = (14, 18, 22), (255, 122, 0), (0, 229, 255)
    r_corner = size * 0.22
    for y in range(size):
        for x in range(size):
            # rounded-rect mask
            dx = max(r_corner - x, x - (size - 1 - r_corner), 0)
            dy = max(r_corner - y, y - (size - 1 - r_corner), 0)
            i = (y * size + x) * 4
            if dx * dx + dy * dy > r_corner * r_corner:
                px[i + 3] = 0
                continue
            px[i:i + 4] = bytes(bg) + b'\xff'

    def stamp(cx, cy, rad, col):
        x0, x1 = max(0, int(cx - rad)), min(size - 1, int(cx + rad) + 1)
        y0, y1 = max(0, int(cy - rad)), min(size - 1, int(cy + rad) + 1)
        for y in range(y0, y1):
            for x in range(x0, x1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= rad * rad:
                    i = (y * size + x) * 4
                    if px[i + 3]:
                        px[i:i + 3] = bytes(col)

    # winding trail path
    pts = [(0.18, 0.82), (0.32, 0.60), (0.52, 0.72), (0.68, 0.45), (0.55, 0.30), (0.78, 0.18)]
    lw = size * 0.055
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        steps = int(math.hypot(bx - ax, by - ay) * size)
        for s in range(steps + 1):
            t = s / max(1, steps)
            stamp((ax + (bx - ax) * t) * size, (ay + (by - ay) * t) * size, lw, orange)
    # position dot at trail end
    stamp(0.78 * size, 0.18 * size, size * 0.09, cyan)
    stamp(0.78 * size, 0.18 * size, size * 0.05, (255, 255, 255))

    open(path, 'wb').write(png(size, size, px))
    print('wrote', path)

make(192, 'icon-192.png')
make(512, 'icon-512.png')
