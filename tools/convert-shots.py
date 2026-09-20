#!/usr/bin/env python3
"""Скриншоты приложения -> WebP для сайта.

Использование:

    python tools/convert-shots.py [папка_со_скриншотами]

Папка по умолчанию — `../OSE_pic` рядом с репозиторием сайта. Результат кладётся
в `assets/img` под именами, которые уже прописаны в разметке обеих языковых версий.

Зависимость — только Pillow (`pip install Pillow`), и только для этого инструмента:
`check-site.py` обходится стандартной библиотекой.

Правила:

* Размер картинки не меняется: по нему выставлены `width`/`height` в разметке
  (их сверяет `check-site.py`), а лайтбокс показывает снимок крупно.
* Кадры интерфейса сохраняются без потерь — текст и тонкие линии остаются резкими.
* «Игровые» кадры с фотографическим содержимым идут в качестве 90: без потерь они
  весят 1.4–1.7 МБ против 200–300 КБ без видимой разницы.

После конвертации:

    python .github/check-site.py
"""

import io
import os
import sys
import time

from PIL import Image

# PNG в папке скриншотов -> имя, которое ждёт разметка.
# Не конвертируются снимки, убранные из галереи: `OSE_wheel_new.png` (Колесо Фортуны),
# `remote1.png` и `remote2.png` (их заменил один `remote_full.png`), `poll.png`
# (та же сцена голосования, что в `poll2.png`, только с другим типом диаграммы).
PAIRS = [
    ('main.png', 'main.webp'),                  # hero: редактор раскладки
    # галерея #screens — в том же порядке, что на странице
    ('ED_3.png', 'ed-3.webp'),
    ('stream_sc.png', 'stream-sc.webp'),
    ('poll2.png', 'poll2.webp'),
    ('scene.png', 'scene.webp'),
    ('term.png', 'term.webp'),
    ('history.png', 'history.webp'),
    ('wheel_cfg.png', 'wheel-cfg.webp'),
    ('HUD_mode.png', 'hud-mode.webp'),
    ('remote_full.png', 'remote-full.webp'),    # пульт целиком: заменяет remote1 и remote2
]

# Выше этого размера сохранять без потерь уже невыгодно
LOSSLESS_LIMIT = 400 * 1024

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(REPO, 'assets', 'img')
DEFAULT_SRC = os.path.join(os.path.dirname(REPO), 'OSE_pic')


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

    print(f'{"файл":<16}{"размер":<12}{"режим":<10}{"вес":>8}')
    for src_name, dst_name in PAIRS:
        src = os.path.join(src_dir, src_name)
        if not os.path.exists(src):
            missing.append(src_name)
            continue

        img = Image.open(src).convert('RGB')
        width, height = img.size
        dst = os.path.join(DST, dst_name)

        if encoded_size(img, lossless=True) <= LOSSLESS_LIMIT:
            save(img, dst, lossless=True)
            mode = 'lossless'
        else:
            save(img, dst, quality=90)
            mode = 'q90'

        size = os.path.getsize(dst)
        total += size
        print(f'{dst_name:<16}{width}x{height:<7}{mode:<10}{size / 1024:>6.0f} КБ')

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
