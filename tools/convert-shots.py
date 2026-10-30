#!/usr/bin/env python3
"""Скриншоты приложения -> WebP для сайта.

Использование:

    python tools/convert-shots.py [папка_со_скриншотами]

Папка по умолчанию — `../OSE_pic` рядом с репозиторием сайта. Результат кладётся
в `assets/img/ru` и `assets/img/en` под именами, которые уже прописаны в разметке
соответствующей языковой версии.

Зависимость — только Pillow (`pip install Pillow`), и только для этого инструмента:
`check-site.py` обходится стандартной библиотекой.

Правила:

* Размер картинки не меняется: по нему выставлены `width`/`height` в разметке
  (их сверяет `check-site.py`), а лайтбокс показывает снимок крупно.
* Кадры панели управления сохраняются без потерь — текст и тонкие линии остаются
  резкими.
* Оверлеи идут в качестве 90: на чёрном фоне разница не видна, а без потерь
  кадр весит в несколько раз больше.

После конвертации:

    python .github/check-site.py
"""

import io
import os
import sys
import time

from PIL import Image

# Снимок панели: без потерь, интерфейсный текст.
PANEL = ['editor', 'themes', 'guests', 'integrations', 'scenes', 'terminal', 'help']

# Оверлей в теме: качество 90, подложка — чёрная сцена.
THEMES = ['nebula', 'orbital', 'elite', 'pixel', 'nuclear', 'teso', 'wardogs', 'retrowave']

LANGS = ['ru', 'en']

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(REPO, 'assets', 'img')
DEFAULT_SRC = os.path.join(os.path.dirname(REPO), 'OSE_pic')


def pairs():
    """PNG в папке скриншотов -> путь, который ждёт разметка."""
    for lang in LANGS:
        for name in PANEL:
            yield f'panel-{lang}-{name}.png', os.path.join(lang, f'{name}.webp'), 'lossless'
        for theme in THEMES:
            yield f'overlay-{lang}-{theme}.png', os.path.join(lang, f'overlay-{theme}.webp'), 'q90'


def encoded_size(img, **kwargs):
    """Вес результата без записи на диск."""
    buf = io.BytesIO()
    img.save(buf, 'WEBP', method=6, **kwargs)
    return buf.tell()


def save(img, dst, **kwargs):
    """Запись с повтором: на Windows свежий файл иногда придерживает антивирус."""
    for attempt in range(5):
        try:
            img.save(dst, 'WEBP', method=6, **kwargs)
            return
        except OSError:
            if attempt == 4:
                raise
            time.sleep(0.3)


def convert(src_dir):
    missing = []
    total = 0
    os.makedirs(DST, exist_ok=True)

    print(f'{"файл":<28}{"размер":<12}{"режим":<10}{"вес":>8}')
    for src_name, dst_name, mode in pairs():
        src = os.path.join(src_dir, src_name)
        if not os.path.exists(src):
            missing.append(src_name)
            continue

        img = Image.open(src).convert('RGB')
        width, height = img.size
        dst = os.path.join(DST, dst_name)
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        if mode == 'lossless':
            save(img, dst, lossless=True)
        else:
            save(img, dst, quality=90)

        size = os.path.getsize(dst)
        total += size
        print(f'{dst_name:<28}{width}x{height:<7}{mode:<10}{size / 1024:>6.0f} КБ')

    print(f'итого: {total / 1024:.0f} КБ в {DST}')
    if missing:
        print(f'не найдены в {src_dir}: {", ".join(missing)}')
        return 1
    return 0


def main():
    src_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    if not os.path.isdir(src_dir):
        print(f'нет такой папки: {src_dir}')
        print('укажите её первым аргументом: python tools/convert-shots.py D:\\pics')
        return 1
    return convert(src_dir)


if __name__ == '__main__':
    sys.exit(main())
