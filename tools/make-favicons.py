#!/usr/bin/env python3
"""Растровые иконки сайта: favicon.ico, favicon-192.png, favicon-512.png.

    python tools/make-favicons.py

Знак рисуется кодом по геометрии из `assets/img/app.svg` — те же два синих клина
на тёмном фоне, но без надписи «OSE»: на 16–48 px она превращается в грязное
пятно, а клинья читаются и там. Крупные формы остаются полным знаком:
`apple-touch-icon.png` (iOS) и `og.png` (соцсети) — на них надпись видна.

Почему рисуем, а не рендерим SVG: рендерить его здесь нечем (ни cairosvg, ни
ImageMagick в системе нет). Поэтому геометрия задана и здесь, и в `app.svg` —
если клинья в знаке изменятся, поправьте координаты в обоих местах.

Тени из `app.svg` не переносятся: на мелком размере их не видно, а края мажут.

После правок:

    python .github/check-site.py
"""

import os
import sys

from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(REPO, 'assets', 'img')

# Холст и клинья — как в app.svg (там 1024x1024 и те же пропорции)
MASTER = 1024
BACKGROUND = '#111318'
LEFT_WEDGE = '#005FAF'
RIGHT_WEDGE = '#386595'
LEFT_POINTS = [(0, 0), (256, 0), (154, 1024), (0, 1024)]
RIGHT_POINTS = [(1024, 0), (768, 0), (870, 1024), (1024, 1024)]

ICO_SIZES = (16, 32, 48)
PNG_SIZES = (192, 512)


def draw_mark():
    """Знак крупно — уменьшать будем одним хорошим фильтром."""
    img = Image.new('RGB', (MASTER, MASTER), BACKGROUND)
    draw = ImageDraw.Draw(img)
    draw.polygon(LEFT_POINTS, fill=LEFT_WEDGE)
    draw.polygon(RIGHT_POINTS, fill=RIGHT_WEDGE)
    return img


def kb(path):
    return os.path.getsize(path) / 1024


def main():
    mark = draw_mark()

    # В корне сайта: сюда смотрит слепой запрос за /favicon.ico
    ico_path = os.path.join(REPO, 'favicon.ico')
    mark.save(ico_path, 'ICO', sizes=[(size, size) for size in ICO_SIZES])
    sizes = ', '.join(str(size) for size in ICO_SIZES)
    print(f'favicon.ico ({sizes}) — {kb(ico_path):.1f} КБ')

    for size in PNG_SIZES:
        png_path = os.path.join(IMG, f'favicon-{size}.png')
        mark.resize((size, size), Image.Resampling.LANCZOS).save(png_path, 'PNG', optimize=True)
        print(f'favicon-{size}.png — {kb(png_path):.1f} КБ')
    return 0


if __name__ == '__main__':
    sys.exit(main())
