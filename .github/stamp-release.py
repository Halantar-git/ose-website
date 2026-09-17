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
API = 'https://api.github.com/repos/%s/releases/latest' % REPO
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

# Кнопки систем в нижнем ряду: href стоит до data-атрибута.
# Главную кнопку скрипт не трогает: какая система у посетителя, знает только браузер,
# поэтому её адрес выбирает main.js из кнопки нужной системы.
SYSTEM = r'(<a class="btn btn-ghost btn-os" href=")[^"]*("[^>]*data-download-os="%s")'


def load_release(path=None):
    if path:
        with open(path, encoding='utf-8') as handle:
            return json.load(handle)

    request = urllib.request.Request(API)
    request.add_header('accept', 'application/vnd.github+json')
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        request.add_header('authorization', 'Bearer %s' % token)

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

    tag = str(release.get('tag_name') or '')
    version = tag[1:] if tag.startswith('v') else tag

    if version:
        html, count = re.subn(r'(<span data-release-version>)[^<]*', r'\g<1>' + version, html)
        if count:
            changes.append('версия %s (в %d местах)' % (version, count))

    parts = str(release.get('published_at') or '')[:10].split('-')
    month = MONTHS[int(parts[1]) - 1] if len(parts) == 3 and parts[1].isdigit() and 1 <= int(parts[1]) <= 12 else ''

    if month:
        date = '%d %s %s' % (int(parts[2]), month, parts[0])
        html, count = re.subn(r'(<span data-release-date>)[^<]*', r'\g<1>' + date, html)
        if count:
            changes.append('дата %s (в %d местах)' % (date, count))

    assets = release.get('assets') or []
    for key, patterns in ASSETS.items():
        asset = pick_asset(assets, patterns)
        url = asset.get('browser_download_url') if asset else ''

        if not url:
            changes.append('%s — файл не найден в релизе' % key)
            continue

        html, count = re.subn(SYSTEM % key, r'\g<1>' + url + r'\g<2>', html)
        if count:
            changes.append('%s → %s' % (key, asset['name']))

    return html, changes


def main():
    release_path = sys.argv[1] if len(sys.argv) > 1 else None
    page_path = sys.argv[2] if len(sys.argv) > 2 else PAGE

    try:
        release = load_release(release_path)
    except Exception as error:  # noqa: BLE001 — любая беда с сетью или файлом: просто не трогаем страницу
        print('релиз не получен: %s' % error)
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
        print('· %s' % change)

    return 0


if __name__ == '__main__':
    sys.exit(main())
