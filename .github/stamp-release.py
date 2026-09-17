#!/usr/bin/env python3
"""Подставляет в index.html версию, дату и ссылки на файлы последнего релиза.

Запускается в workflow перед выкладкой на GitHub Pages: у посетителя страница
получает уже готовые значения, поэтому кнопки скачивания не зависят от запроса
к API (у него лимит 60 запросов в час на IP, и он легко исчерпывается).

    python3 .github/stamp-release.py                 # релиз из API, правка index.html
    python3 .github/stamp-release.py dump.json page.html   # из файла, для проверки

Если релиз получить не удалось, файл остаётся как есть: выкладку это не сломает.
"""

import json
import os
import re
import sys
import urllib.request

REPO = 'Halantar-git/open-stream-environment'
API = f'https://api.github.com/repos/{REPO}/releases/latest'
PAGE = 'index.html'
TIMEOUT = 20

MONTHS = [
    'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
    'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
]

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

    parts = str(release.get('published_at') or '')[:10].split('-')
    month = MONTHS[int(parts[1]) - 1] if len(parts) == 3 and parts[1].isdigit() and 1 <= int(parts[1]) <= 12 else ''

    if month:
        date = f'{int(parts[2])} {month} {parts[0]}'
        html, count = re.subn(r'(<span data-release-date>)[^<]*', rf'\g<1>{date}', html)
        if count:
            changes.append(f'дата {date} (в {count} местах)')
        else:
            changes.append('дата — места в разметке не нашлось')

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


def main():
    release_path = sys.argv[1] if len(sys.argv) > 1 else None
    page_path = sys.argv[2] if len(sys.argv) > 2 else PAGE

    try:
        release = load_release(release_path)
    # нет файла, нет сети, битый JSON — в любом из этих случаев просто не трогаем страницу
    except (OSError, ValueError) as error:
        print(f'релиз не получен: {error}')
        return 0

    with open(page_path, encoding='utf-8') as handle:
        html = handle.read()

    stamped, changes = stamp(html, release)

    if not changes:
        print('в разметке не нашлось мест для подстановки')
        return 0

    if stamped != html:
        with open(page_path, 'w', encoding='utf-8', newline='') as handle:
            handle.write(stamped)

    for change in changes:
        print(f'· {change}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
