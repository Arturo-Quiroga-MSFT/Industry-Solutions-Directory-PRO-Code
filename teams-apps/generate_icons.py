#!/usr/bin/env python3
"""Generate MSD-branded PNG icons for Teams app packages."""
import struct, zlib, os

# Simple 5x7 pixel font for uppercase letters
FONT = {
    'M': [
        "X...X",
        "XX.XX",
        "X.X.X",
        "X...X",
        "X...X",
        "X...X",
        "X...X",
    ],
    'S': [
        ".XXX.",
        "X....",
        "X....",
        ".XXX.",
        "....X",
        "....X",
        ".XXX.",
    ],
    'D': [
        "XXXX.",
        "X...X",
        "X...X",
        "X...X",
        "X...X",
        "X...X",
        "XXXX.",
    ],
}

def render_text(text, scale, canvas_w, canvas_h, fg, bg):
    """Render text centered on a canvas, return pixel rows."""
    char_w, char_h = 5, 7
    spacing = 1
    total_w = len(text) * char_w + (len(text) - 1) * spacing
    total_h = char_h
    # Scale to fit ~60% of canvas width
    if scale == 0:
        scale = max(1, int(canvas_w * 0.6 / total_w))
    sw = total_w * scale
    sh = total_h * scale
    ox = (canvas_w - sw) // 2
    oy = (canvas_h - sh) // 2

    pixels = [[bg] * canvas_w for _ in range(canvas_h)]
    for ci, ch in enumerate(text):
        glyph = FONT.get(ch, FONT['M'])
        gx = ci * (char_w + spacing)
        for gy, row in enumerate(glyph):
            for gxx, cell in enumerate(row):
                if cell == 'X':
                    for sy in range(scale):
                        for sx in range(scale):
                            px = ox + (gx + gxx) * scale + sx
                            py = oy + (gy) * scale + sy
                            if 0 <= px < canvas_w and 0 <= py < canvas_h:
                                pixels[py][px] = fg
    return pixels

def create_png_with_text(path, width, height, fg, bg, text="MSD"):
    """Create a PNG with text rendered on a colored background."""
    def chunk(ct, data):
        c = ct + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    pixels = render_text(text, 0, width, height, fg, bg)

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
    raw = b''
    for row in pixels:
        raw += b'\x00'
        for r, g, b_val, a in row:
            raw += bytes([r, g, b_val, a])
    idat = chunk(b'IDAT', zlib.compress(raw))
    iend = chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(header + ihdr + idat + iend)

# Seller icons (indigo bg, white text)
seller_bg = (79, 70, 229, 255)
seller_fg = (255, 255, 255, 255)
create_png_with_text('seller/color.png', 192, 192, seller_fg, seller_bg)
create_png_with_text('seller/outline.png', 32, 32, seller_fg, seller_bg)

# Customer icons (sky blue bg, white text)
customer_bg = (14, 165, 233, 255)
customer_fg = (255, 255, 255, 255)
create_png_with_text('customer/color.png', 192, 192, customer_fg, customer_bg)
create_png_with_text('customer/outline.png', 32, 32, customer_fg, customer_bg)

print("MSD-branded icons created (4 files)")
