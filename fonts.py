"""Use an installed font without redistributing proprietary font files."""
from pathlib import Path
from PIL import ImageFont

def label_font(size):
    for name in ('C:/Windows/Fonts/arial.ttf',
                 '/System/Library/Fonts/Supplemental/Arial.ttf',
                 '/System/Library/Fonts/Helvetica.ttc'):
        if Path(name).is_file():
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                pass
    return ImageFont.load_default(size=size)
