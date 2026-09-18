#!/usr/bin/env python3
"""Проверки статического сайта перед выкладкой.

    python3 .github/check-site.py

Проверяет то, что не поймает ни один линтер разметки, но что реально ломает
страницу у посетителя:

  * все локальные ссылки и картинки из HTML существуют на диске;
  * размеры <img> в разметке совпадают с размерами файлов (иначе вёрстка
    прыгает при загрузке, а картинка растягивается);
  * og:image совпадает по размеру со своим файлом;
  * места для подстановки релиза (версия, дата, кнопки) на месте;
  * stamp-release.py действительно подставляет данные тестового релиза.

Зависимостей нет — только стандартная библиотека. Код возврата 1, если что-то
не сошлось.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ['index.html', 'privacy.html', '404.html']

LINK = re.compile(r'(?:src|href)="([^"]*)"')
IMG = re.compile(r'<img\b[^>]*>', re.IGNORECASE)
ATTR = re.compile(r'(\w[\w-]*)="([^"]*)"')

RASTER = ('.png', '.jpg', '.jpeg', '.webp')
SKIP_SCHEMES = ('http://', 'https://', '//', 'mailto:', 'tel:', 'data:', 'javascript:')

# Кнопок скачивания и мест под версию с датой — по три (по одной на систему)
PLACEHOLDERS = {'data-release-version': 3, 'data-release-date': 3, 'data-download-os': 3}

errors: list[str] = []
notes: list[str] = []


def fail(message):
    errors.append(message)


def read(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def strip_target(target):
    for cut in ('#', '?'):
        index = target.find(cut)
        if index != -1:
            target = target[:index]
    return target.strip()


def resolves_to(page, target):
    """Существует ли то, на что ссылается страница. None — ссылка внешняя."""
    target = strip_target(target)
    if not target or target.startswith(SKIP_SCHEMES):
        return None

    path = os.path.normpath(os.path.join(os.path.dirname(page), target))
    if target.endswith('/') or os.path.isdir(os.path.join(ROOT, path)):
        path = os.path.join(path, 'index.html')
    return os.path.isfile(os.path.join(ROOT, path))


def png_size(blob):
    return int.from_bytes(blob[16:20], 'big'), int.from_bytes(blob[20:24], 'big')


def webp_size(blob):
    fourcc = blob[12:16]
    if fourcc == b'VP8 ':
        width = int.from_bytes(blob[26:28], 'little') & 0x3FFF
        height = int.from_bytes(blob[28:30], 'little') & 0x3FFF
    elif fourcc == b'VP8L':
        bits = int.from_bytes(blob[21:25], 'little')
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
    elif fourcc == b'VP8X':
        width = int.from_bytes(blob[24:27], 'little') + 1
        height = int.from_bytes(blob[27:30], 'little') + 1
    else:
        return None
    return width, height


def svg_size(text):
    tag = re.search(r'<svg\b[^>]*>', text, re.IGNORECASE)
    if not tag:
        return None

    attributes = dict(ATTR.findall(tag.group(0)))
    try:
        return round(float(attributes['width'])), round(float(attributes['height']))
    except (KeyError, ValueError):
        pass

    try:
        _, _, width, height = attributes['viewBox'].replace(',', ' ').split()
        return round(float(width)), round(float(height))
    except (KeyError, ValueError):
        return None


def image_size(path):
    with open(path, 'rb') as handle:
        blob = handle.read(64)

    if blob[:8] == b'\x89PNG\r\n\x1a\n':
        return png_size(blob)
    if blob[:4] == b'RIFF' and blob[8:12] == b'WEBP':
        return webp_size(blob)
    if path.lower().endswith('.svg'):
        return svg_size(read(path))
    return None


def check_links(page):
    html = read(os.path.join(ROOT, page))
    for target in set(LINK.findall(html)):
        if resolves_to(page, target) is False:
            fail(f'{page}: ссылка «{target}» никуда не ведёт')


def check_image_sizes(page):
    html = read(os.path.join(ROOT, page))
    for tag in IMG.findall(html):
        attributes = dict(ATTR.findall(tag))
        src = strip_target(attributes.get('src', ''))
        if not src or src.startswith(SKIP_SCHEMES) or not src.lower().endswith(RASTER):
            continue
        # Значки отрисованы мелким размером поверх крупного SVG — их не сверяем
        if int(attributes.get('width') or 0) <= 64 or 'height' not in attributes:
            continue

        path = os.path.join(ROOT, os.path.normpath(os.path.join(os.path.dirname(page), src)))
        if not os.path.isfile(path):
            continue

        declared = int(attributes['width']), int(attributes['height'])
        real = image_size(path)
        if real is None:
            notes.append(f'{page}: не разобрал размеры {src}')
        elif real != declared:
            fail(f'{page}: у {src} в разметке {declared[0]}x{declared[1]}, '
                 f'а в файле {real[0]}x{real[1]}')


def check_og_image(html):
    width = re.search(r'property="og:image:width" content="(\d+)"', html)
    height = re.search(r'property="og:image:height" content="(\d+)"', html)
    url = re.search(r'property="og:image" content="[^"]*?([^/"]+)"', html)
    if not (width and height and url):
        fail('index.html: нет og:image или его размеров')
        return

    name = url.group(1)
    path = os.path.join(ROOT, 'assets', 'img', name)
    if not os.path.isfile(path):
        fail(f'index.html: og:image ссылается на несуществующий {name}')
        return

    real = image_size(path)
    if real and real != (int(width.group(1)), int(height.group(1))):
        fail(f'index.html: og:image заявлено {width.group(1)}x{height.group(1)}, '
             f'а в файле {real[0]}x{real[1]}')


def check_placeholders(html):
    for name, expected in PLACEHOLDERS.items():
        found = len(re.findall(name, html))
        if found != expected:
            fail(f'index.html: мест с {name} — {found}, ожидалось {expected}')


def check_stamp(index_html):
    """Прогоняет stamp-release.py на поддельном релизе: файл не должен испортиться."""
    fixture = {
        'tag_name': 'v9.9.9',
        'published_at': '2026-01-05T10:00:00Z',
        'assets': [
            {'name': 'ose-setup.exe', 'browser_download_url': 'https://example.invalid/w.exe'},
            {'name': 'ose.AppImage', 'browser_download_url': 'https://example.invalid/l.AppImage'},
            {'name': 'ose.dmg', 'browser_download_url': 'https://example.invalid/m.dmg'},
        ],
    }

    room = tempfile.mkdtemp(prefix='ose-check-')
    try:
        json_path = os.path.join(room, 'release.json')
        page_path = os.path.join(room, 'page.html')
        with open(json_path, 'w', encoding='utf-8') as handle:
            json.dump(fixture, handle)
        with open(page_path, 'w', encoding='utf-8') as handle:
            handle.write(index_html)

        done = subprocess.run(
            [sys.executable, os.path.join('.github', 'stamp-release.py'), json_path, page_path],
            cwd=ROOT, capture_output=True, encoding='utf-8', errors='replace',
            timeout=60, check=False,
        )
        if done.returncode != 0:
            fail(f'stamp-release.py упал: {done.stderr.strip() or done.stdout.strip()}')
            return

        stamped = read(page_path)
        for probe in ('9.9.9', '5 января 2026', '"softwareVersion": "9.9.9"',
                      'https://example.invalid/w.exe',
                      'https://example.invalid/l.AppImage', 'https://example.invalid/m.dmg'):
            if probe not in stamped:
                fail(f'stamp-release.py не подставил «{probe}»')
    except subprocess.TimeoutExpired:
        fail('stamp-release.py не ответил за минуту')
    finally:
        shutil.rmtree(room, ignore_errors=True)


def force_utf8_output():
    """В консоли Windows кодировка вывода не UTF-8, и печать падает на «→»."""
    reconfigure = getattr(sys.stdout, 'reconfigure', None)
    if reconfigure is not None:
        reconfigure(encoding='utf-8', errors='replace')


def main():
    force_utf8_output()

    for page in PAGES:
        if not os.path.isfile(os.path.join(ROOT, page)):
            fail(f'нет страницы {page}')
            continue
        check_links(page)
        check_image_sizes(page)

    index_html = read(os.path.join(ROOT, 'index.html'))
    check_og_image(index_html)
    check_placeholders(index_html)
    check_stamp(index_html)

    for note in notes:
        print(f'? {note}')
    for message in errors:
        print(f'! {message}')

    if errors:
        print(f'\nне прошло проверок: {len(errors)}')
        return 1

    print('всё сошлось: ссылки, размеры картинок, места подстановки и сам подстановщик')
    return 0


if __name__ == '__main__':
    sys.exit(main())
