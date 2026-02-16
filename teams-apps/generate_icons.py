#!/usr/bin/env python3
"""Generate placeholder PNG icons for Teams app packages."""
import struct, zlib, os

def create_png(path, width, height, r, g, b, a=255):
    """Create a minimal solid-color PNG file using only stdlib."""
    def chunk(ct, data):
        c = ct + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
    raw = b''
    for y in range(height):
        raw += b'\x00'
        for x in range(width):
            raw += bytes([r, g, b, a])
    idat = chunk(b'IDAT', zlib.compress(raw))
    iend = chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(header + ihdr + idat + iend)

# Seller icons (indigo)
create_png('seller/color.png', 192, 192, 79, 70, 229)
create_png('seller/outline.png', 32, 32, 79, 70, 229)

# Customer icons (sky blue)
create_png('customer/color.png', 192, 192, 14, 165, 233)
create_png('customer/outline.png', 32, 32, 14, 165, 233)

print("Placeholder icons created (4 files)")
