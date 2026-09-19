#!/usr/bin/env python3
"""Подставляет в страницы сайта версию, дату и ссылки на файлы последнего релиза.

Запускается в workflow перед выкладкой на GitHub Pages: у посетителя страница
получает уже готовые значения, поэтому кнопки скачивания не зависят от запроса
к API (у него лимит 60 запросов в час на IP, и он легко исчерпывается).

Правятся обе языковые версии — index.html и en/index.html. Язык берётся из
<html lang="..."> самой страницы, потому что дата в них разная: «16 сентября
2026» против «September 16, 2026».

    python3 .github/stamp-release.py                 # релиз из API, все страницы
    python3 .github/stamp-release.py dump.json page.html   # из файла, для проверки

Если релиз получить не удалось, файлы остаются как есть: выкладку это не сломает.
"""

import json
import os
import re
import sys
import urllib.request

REPO = 'Halantar-git/open-stream-environment'
API = f'https://api.github.com/repos/{REPO}/releases/latest'
PAGES = ['index.html', 'en/index.html']
TIMEOUT = 20

MONTHS = {
    'ru': [
        'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
        'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря',
    ],
    'en': [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December',
    ],
}

# Файлы под каждую систему — в порядке предпочтения (те же шаблоны, что в main.js)
ASSETS = {
    'windows': [r'-setup\.exe$', r'\.exe$'],
    'linux': [r'\.AppImage$', r'\.deb$'],
    'macos': [r'\.dmg$', r'-mac\.zip$'],
}

# Кнопки систем: href стоит до data-атрибута, а список классов может меняться
# (btn-lg и т.п.), поэтому ловим по btn-os, а не по полному class.
SYSTEM = r'(<a class="[^"]*btn-os[^"]*" href=")[^"]*("[^>]*data-download-os="{key}")'


def load_release(path=None):
    if path:
        with open(path, encoding='utf-8') as handle:
            return json.load(handle)

    request = urllib.request.Request(API)
    request.add_header('accept', 'application/vnd.github+json')
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        request.add_header('authorization', f'Bearer {token}')

    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.load(response)


def pick_asset(assets, patterns):
    for pattern in patterns:
        for asset in assets:
            if re.search(pattern, asset.get('name', ''), re.IGNORECASE):
                return asset
    return None


def page_language(html):
    """'en' у английской версии, иначе 'ru' — по атрибуту lang у <html>."""
    return 'en' if re.search(r'<html[^>]*\blang="en', html) else 'ru'


def format_date(published_at, lang):
    """«16 сентября 2026» или «September 16, 2026»; пустая строка, если даты нет."""
    parts = str(published_at or '')[:10].split('-')
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return ''

    month = int(parts[1])
    if not 1 <= month <= 12:
        return ''

    if lang == 'en':
        return f'{MONTHS["en"][month - 1]} {int(parts[2])}, {parts[0]}'
    return f'{int(parts[2])} {MONTHS["ru"][month - 1]} {parts[0]}'


def stamp(html, release):
    """Возвращает (html, список правок) — только по тем местам, что нашлись в разметке."""
    changes = []

    version = str(release.get('tag_name') or '').removeprefix('v')

    if version:
        html, count = re.subn(r'(<span data-release-version>)[^<]*', rf'\g<1>{version}', html)
        if count:
            changes.append(f'версия {version} (в {count} местах)')
        else:
            changes.append('версия — места в разметке не нашлось')

        # Та же версия в разметке для поисковиков, у неё нет видимого места
        html, count = re.subn(r'("softwareVersion": ")[^"]*', rf'\g<1>{version}', html)
        changes.append(f'версия {version} в softwareVersion' if count else 'softwareVersion — не нашлось')

    date = format_date(release.get('published_at'), page_language(html))

    if date:
        html, count = re.subn(r'(<span data-release-date>)[^<]*', rf'\g<1>{date}', html)
        if count:
            changes.append(f'дата {date} (в {count} местах)')
        else:
            changes.append('дата — места в разметке не нашлось')
    else:
        changes.append('дата — в релизе её не разобрать')

    assets = release.get('assets') or []
    for key, patterns in ASSETS.items():
        asset = pick_asset(assets, patterns)

        if not asset:
            changes.append(f'{key} — файл не найден в релизе')
            continue

        url = asset.get('browser_download_url') or ''

        if not url:
            changes.append(f'{key} — у файла нет адреса для скачивания')
            continue

        html, count = re.subn(SYSTEM.format(key=key), rf'\g<1>{url}\g<2>', html)
        if count:
            changes.append(f'{key} → {asset["name"]}')
        else:
            changes.append(f'{key} — кнопки в разметке не нашлось')

    return html, changes


def force_utf8_output():
    """В консоли Windows кодировка вывода не UTF-8, и печать падает на «→»."""
    reconfigure = getattr(sys.stdout, 'reconfigure', None)
    if reconfigure is not None:
        reconfigure(encoding='utf-8', errors='replace')


def main():
    force_utf8_output()

    release_path = sys.argv[1] if len(sys.argv) > 1 else None
    # без аргументов — все страницы сайта; с фикстурой — те же страницы, если не названы явно
    pages = sys.argv[2:] or PAGES

    try:
        release = load_release(release_path)
    # нет файла, нет сети, битый JSON — в любом из этих случаев просто не трогаем страницы
    except (OSError, ValueError) as error:
        print(f'релиз не получен: {error}')
        return 0

    for page_path in pages:
        if not os.path.isfile(page_path):
            print(f'{page_path} — файла нет, пропускаю')
            continue

        with open(page_path, encoding='utf-8') as handle:
            html = handle.read()

        stamped, changes = stamp(html, release)

        if not changes:
            print(f'{page_path} — мест для подстановки не нашлось')
            continue

        if stamped != html:
            with open(page_path, 'w', encoding='utf-8', newline='') as handle:
                handle.write(stamped)

        print(f'{page_path}:')
        for change in changes:
            print(f'· {change}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
