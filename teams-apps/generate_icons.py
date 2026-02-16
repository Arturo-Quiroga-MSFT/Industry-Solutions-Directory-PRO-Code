#!/usr/bin/env python3
"""Generate distinct MSD-branded PNG icons for Teams app packages.

Seller app:   Indigo background + bar chart icon   (analytics / partner insights)
Customer app: Sky blue background + magnifying glass icon (solution discovery)

Color icons (192×192): rounded rect bg + icon + "MSD" label
Outline icons (32×32): white icon on transparent bg (Teams requirement)
"""
import struct, zlib, math, os

# ---------------------------------------------------------------------------
# PNG helpers
# ---------------------------------------------------------------------------

def _png_chunk(chunk_type, data):
    c = chunk_type + data
    return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)


def save_png(path, pixels, width, height):
    """Write RGBA pixel grid to a PNG file."""
    header = b'\x89PNG\r\n\x1a\n'
    ihdr = _png_chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
    raw = b''
    for row in pixels:
        raw += b'\x00'
        for r, g, b, a in row:
            raw += bytes([r, g, b, a])
    idat = _png_chunk(b'IDAT', zlib.compress(raw))
    iend = _png_chunk(b'IEND', b'')
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'wb') as f:
        f.write(header + ihdr + idat + iend)

# ---------------------------------------------------------------------------
# Drawing primitives
# ---------------------------------------------------------------------------

def canvas(w, h, bg=(0, 0, 0, 0)):
    return [[bg] * w for _ in range(h)]


def _set(px, x, y, c):
    if 0 <= x < len(px[0]) and 0 <= y < len(px):
        px[y][x] = c


def fill_rect(px, x1, y1, x2, y2, c):
    for y in range(max(0, y1), min(len(px), y2)):
        for x in range(max(0, x1), min(len(px[0]), x2)):
            px[y][x] = c


def fill_rounded_rect(px, x1, y1, x2, y2, r, c):
    for y in range(max(0, y1), min(len(px), y2)):
        for x in range(max(0, x1), min(len(px[0]), x2)):
            inside = True
            if x < x1 + r and y < y1 + r:
                inside = (x - (x1 + r)) ** 2 + (y - (y1 + r)) ** 2 <= r * r
            elif x >= x2 - r and y < y1 + r:
                inside = (x - (x2 - r - 1)) ** 2 + (y - (y1 + r)) ** 2 <= r * r
            elif x < x1 + r and y >= y2 - r:
                inside = (x - (x1 + r)) ** 2 + (y - (y2 - r - 1)) ** 2 <= r * r
            elif x >= x2 - r and y >= y2 - r:
                inside = (x - (x2 - r - 1)) ** 2 + (y - (y2 - r - 1)) ** 2 <= r * r
            if inside:
                px[y][x] = c


def fill_circle(px, cx, cy, r, c):
    for y in range(cy - r - 1, cy + r + 2):
        for x in range(cx - r - 1, cx + r + 2):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                _set(px, x, y, c)


def draw_ring(px, cx, cy, r_out, r_in, c):
    for y in range(cy - r_out - 1, cy + r_out + 2):
        for x in range(cx - r_out - 1, cx + r_out + 2):
            d = (x - cx) ** 2 + (y - cy) ** 2
            if r_in * r_in <= d <= r_out * r_out:
                _set(px, x, y, c)


def draw_thick_line(px, x1, y1, x2, y2, thickness, c):
    length = max(1, int(math.hypot(x2 - x1, y2 - y1)))
    for t in range(length + 1):
        frac = t / length
        x = int(x1 + frac * (x2 - x1))
        y = int(y1 + frac * (y2 - y1))
        fill_circle(px, x, y, thickness // 2, c)


# ---------------------------------------------------------------------------
# 5×7 pixel font for "MSD" label
# ---------------------------------------------------------------------------

FONT = {
    'M': ["X...X", "XX.XX", "X.X.X", "X...X", "X...X", "X...X", "X...X"],
    'S': [".XXX.", "X....", "X....", ".XXX.", "....X", "....X", ".XXX."],
    'D': ["XXXX.", "X...X", "X...X", "X...X", "X...X", "X...X", "XXXX."],
}


def draw_text(px, text, cx, top_y, scale, c):
    """Draw text centered horizontally at cx, starting at top_y."""
    char_w, char_h, spacing = 5, 7, 1
    total_w = len(text) * char_w + (len(text) - 1) * spacing
    ox = cx - (total_w * scale) // 2
    for ci, ch in enumerate(text):
        glyph = FONT.get(ch, FONT['M'])
        gx = ci * (char_w + spacing)
        for gy, row in enumerate(glyph):
            for gxx, cell in enumerate(row):
                if cell == 'X':
                    for sy in range(scale):
                        for sx in range(scale):
                            _set(px, ox + (gx + gxx) * scale + sx,
                                 top_y + gy * scale + sy, c)


# ---------------------------------------------------------------------------
# Icon composers
# ---------------------------------------------------------------------------

def draw_bar_chart(px, cx, cy, size, c):
    """Three ascending bars representing analytics / insights."""
    bar_w = max(2, size // 5)
    gap = max(1, size // 10)
    heights = [size * 40 // 100, size * 65 // 100, size * 95 // 100]
    total_w = bar_w * 3 + gap * 2
    x_start = cx - total_w // 2
    baseline = cy + size // 2
    for i, h in enumerate(heights):
        bx = x_start + i * (bar_w + gap)
        by = baseline - h
        r = max(1, bar_w // 4)
        fill_rounded_rect(px, bx, by, bx + bar_w, baseline, r, c)


def draw_magnifying_glass(px, cx, cy, size, c):
    """Magnifying glass representing search / discovery."""
    r_out = size * 36 // 100
    r_in = size * 24 // 100
    gcx = cx - size // 8
    gcy = cy - size // 8
    draw_ring(px, gcx, gcy, r_out, r_in, c)
    # Handle from circle edge at 45° toward bottom-right
    angle = math.pi / 4
    sx = gcx + int(r_out * math.cos(angle))
    sy = gcy + int(r_out * math.sin(angle))
    handle_len = size * 38 // 100
    ex = sx + int(handle_len * math.cos(angle))
    ey = sy + int(handle_len * math.sin(angle))
    draw_thick_line(px, sx, sy, ex, ey, max(2, size // 7), c)


# ---------------------------------------------------------------------------
# Build color icon (192×192) — rounded-rect bg + icon + "MSD" label
# ---------------------------------------------------------------------------

def build_color_icon(path, bg_color, fg_color, draw_icon_fn):
    W, H = 192, 192
    px = canvas(W, H, (0, 0, 0, 0))
    pad = 8
    fill_rounded_rect(px, pad, pad, W - pad, H - pad, 28, bg_color)
    # Icon occupies upper area
    icon_size = 80
    icon_cy = 68
    draw_icon_fn(px, W // 2, icon_cy, icon_size, fg_color)
    # "MSD" label below the icon
    draw_text(px, "MSD", W // 2, 128, 5, fg_color)
    save_png(path, px, W, H)


# ---------------------------------------------------------------------------
# Build outline icon (32×32) — white icon on transparent bg
# ---------------------------------------------------------------------------

def build_outline_icon(path, draw_icon_fn):
    W, H = 32, 32
    white = (255, 255, 255, 255)
    px = canvas(W, H, (0, 0, 0, 0))
    draw_icon_fn(px, W // 2, H // 2, 24, white)
    save_png(path, px, W, H)


# ---------------------------------------------------------------------------
# Generate all icons
# ---------------------------------------------------------------------------

INDIGO = (79, 70, 229, 255)
SKY    = (14, 165, 233, 255)
WHITE  = (255, 255, 255, 255)

# Seller — bar chart
build_color_icon('seller/color.png',   INDIGO, WHITE, draw_bar_chart)
build_outline_icon('seller/outline.png', draw_bar_chart)

# Customer — magnifying glass
build_color_icon('customer/color.png', SKY, WHITE, draw_magnifying_glass)
build_outline_icon('customer/outline.png', draw_magnifying_glass)

print("Distinct MSD icons created:")
print("  seller/   → bar chart icon   (indigo #4F46E5)")
print("  customer/ → magnifying glass (sky blue #0EA5E9)")
