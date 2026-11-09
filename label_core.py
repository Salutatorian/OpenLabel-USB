"""Independent raster encoder. No vendor binaries are loaded."""
import math
from PIL import Image

def validate(width, height, gap, copies):
    if not all(math.isfinite(v) for v in (width, height, gap)):
        raise ValueError('Dimensions must be finite numbers.')
    if not (10 <= width <= 104 and 10 <= height <= 300 and 0 <= gap <= 10):
        raise ValueError('Use width 10–104 mm, height 10–300 mm, gap 0–10 mm.')
    if not isinstance(copies, int) or not 1 <= copies <= 20:
        raise ValueError('Copies must be an integer from 1 to 20.')

def make_job(image, width, height, gap, copies, invert=False):
    validate(width, height, gap, copies)
    gray = image.convert('L')
    if gray.width > 832 or gray.height > 2400:
        raise ValueError('Raster exceeds the supported 8 dots/mm label area.')
    stride = (gray.width + 7) // 8
    # TSPL convention: 0 black, 1 white; MSB first. Padding stays white.
    packed = bytearray([255] * (stride * gray.height))
    pix = gray.load()
    for y in range(gray.height):
        for x in range(gray.width):
            black = pix[x, y] < 128
            if invert:
                black = not black
            if black:
                packed[y * stride + x // 8] &= ~(128 >> (x % 8))
    header = (f'SIZE {width:.1f} mm,{height:.1f} mm\r\n'
              f'GAP {gap:.1f} mm,0 mm\r\nREFERENCE 0,0\r\n'
              'DIRECTION 0\r\nCLS\r\n'
              f'BITMAP 0,0,{stride},{gray.height},1,').encode('ascii')
    return header + packed + f'\r\nPRINT 1,{copies}\r\n'.encode('ascii')
