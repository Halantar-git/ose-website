# Open Stream Environment — сайт приложения

Статический лендинг для приложения Open Stream Environment (OSE) на Material Design 3. Без сборки и зависимостей: чистые HTML, CSS и небольшой JS. Публикуется на GitHub Pages.

## Структура

```
index.html                     лендинг
404.html                       страница «не найдено»
.nojekyll                      отключает обработку Jekyll
assets/css/style.css           все стили: M3-токены + компоненты
assets/js/main.js              тема, мобильное меню, ripple, мелочи
assets/img/app.svg             иконка приложения (шапка, подвал, favicon)
.github/workflows/pages.yml    автодеплой на GitHub Pages
```

## Откуда взялся контент

Всё фактическое содержимое сверено с `README.md` и `CHANGELOG.md` приложения (версия 3.2.1, 16 сентября 2026):

- **Hero** — что это Electron-приложение, а оверлей отдаётся локальным сервером и добавляется в OBS как Browser Source.
- **Возможности** — редактор в стиле drag-and-drop, серверная очередь алертов, сцены и пульты, темы с 3D-вариантами, чат с ботом и автомодерацией, локальное хранение с шифрованием секретов.
- **Чипы под карточками** — список виджетов из README.
- **Быстрый старт** — `npm install` / `npm start`, адрес оверлея и настройки Browser Source.
- **FAQ** — требования, подключение Twitch и DonationAlerts, где лежат данные, диагностика донатов, режимы «поверх игры», отчёты для поддержки.
- **Скачать** — артефакты сборки и предупреждение о неподписанных сборках.

Если формулировка разошлась с реальностью приложения — поправьте текст прямо в `index.html`.

## Что нужно заполнить

1. **Лицензия.** Везде указана GPL со ссылкой на файл `LICENSE` в репозитории приложения — в FAQ, блоке «Скачать», подвале и JSON-LD. Если файл называется иначе (`LICENSE.md`, `COPYING`) или у вас GPL-2.0 — поправьте ссылку и текст.
2. **Ссылки уже проставлены** на `github.com/Halantar-git/open-stream-environment`: репозиторий, CHANGELOG, issues, `releases/latest` и README («Как установить»).
3. **Адрес сайта.** В `canonical`, `og:url` и JSON-LD стоит `https://halantar-git.github.io/open-stream-environment/`, в `404.html` — `SITE_ROOT = '/open-stream-environment/'`. Если сайт будет в другом репозитории, поправьте эти четыре места.
4. **Скриншоты.** В hero и в секции `#screens` стоят заглушки-рамки. Положите файлы в `assets/img/` и замените разметку:

   ```html
   <!-- было -->
   <div class="shot"><span>[Экран 1]</span></div>

   <!-- стало -->
   <img class="shot" src="assets/img/screen-1.png" alt="Что видно на экране" loading="lazy" width="1280" height="800">
   ```

   Для hero — вместо блока `<div class="mock">…</div>`:

   ```html
   <img src="assets/img/hero.png" alt="Главный экран приложения" width="1200" height="900">
   ```

   Классы `.mock` и `.shot` уже дают скругления и тональный фон; у `.mock` — ещé и elevation.
5. **Превью для соцсетей.** Положите `assets/img/og.png` (1200×630) и раскомментируйте `og:image` в `<head>`.
6. **Политика конфиденциальности.** Единственная оставшаяся заглушка в подвале. Для сторов такая страница обычно обязательна — можно сделать `privacy.html` по образцу `404.html`.
7. **Иконка.** В шапке, подвале и favicon используется `assets/img/app.svg`. Скругление углов задаётся в CSS (`.brand-mark { border-radius: … }`) — уберите, если хотите показывать её квадратом. Для `apple-touch-icon` iOS нужен PNG 180×180: SVG там не читается, сейчас стоит ссылка на `app.svg`.

## Material Design 3

Стили написаны на официальных M3-токенах (`assets/css/style.css`), без фреймворков и внешних зависимостей.

- **Цветовые роли** по схеме `md.sys.color.*`: `primary` / `on-primary` / `primary-container` / `surface-container-low..highest` / `outline-variant` / `inverse-*` и т.д. Палитра собрана из цветов иконки приложения: `primary` (светлая схема) = `#005FAF`, `secondary` = `#386595` (второй синий с логотипа, он же цвет фокус-ринга), тёмная поверхность и `background` = `#111318`. Остальные роли — производные тона синей шкалы M3.
- **`tertiary`** уведён в сине-голубую часть шкалы: в M3 он по умолчанию фиолетовый, а в логотипе фиолетового нет. В стилях сейчас не используется — это запас на будущее.
- **Тёмная схема** — полный набор ролей; включается по системной настройке или кнопкой в шапке.
- **Типографика** — шкала `md.sys.typescale.*` (display / headline / title / body / label). Заголовки в M3 — Regular (400), а не Bold.
- **Shape** — `corner-extra-small 4` → `corner-extra-large 28` → `corner-full`.
- **Elevation** — уровни 1–3 из спеки, без своих теней.
- **State layers** — hover 8%, focus 10%, pressed 10% через `--md-sys-state-*`; на кнопках и icon button работает ripple (в `main.js`, отключается при `prefers-reduced-motion`).
- **Компоненты**: top app bar, filled и outlined кнопки, icon button, assist chip, elevated cards, expansion panels (FAQ), баннер на `primary-container`, выпадающее меню в мобильной навигации.

### Своя палитра

Возьмите палитру в [Material Theme Builder](https://material-foundation.github.io/material-theme-builder/), экспортируйте CSS-переменные и замените ими блоки `:root`, `@media (prefers-color-scheme: dark)` и `:root[data-theme="dark"]` в начале `assets/css/style.css`. Имена токенов менять не нужно — остальной файл на них и построен.

Иконка приложения (`assets/img/app.svg`) — ваш собственный файл со своими цветами (`#005FAF`, `#386595` на `#111318`); сайт её не перекрашивает, потому что SVG подключён через `<img>` и CSS-переменные внутри него не работают. При смене палитры сайта иконку можно не трогать — это айдентика.

### Шрифт

В `--md-ref-typeface-plain` первым стоит `Roboto`, но извне он **не подгружается** — сайт остаётся без сторонних запросов. На Android и ChromeOS Roboto есть в системе, на Windows и macOS подставится системный шрифт. Если нужен Roboto везде, добавьте в `<head>`:

```html
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap">
```

## Локальный просмотр

Достаточно открыть `index.html` в браузере. Если нужен http-сервер:

```sh
python -m http.server 8000
```

## Публикация на GitHub Pages

1. Запушьте репозиторий в GitHub (ветка `main`).
2. Включите Pages: **Settings → Pages → Source → GitHub Actions**. Шаг обязательный — без него
   `main` останется без сайта, а workflow упадёт на `configure-pages`. То же самое из командной строки:

   ```sh
   gh api -X POST repos/Halantar-git/ose-website/pages -f build_type=workflow
   ```
3. После пуша в `main` workflow `.github/workflows/pages.yml` соберёт и опубликует сайт.
   Адрес появится в **Settings → Pages**, обычно `https://<логин>.github.io/<репозиторий>/`.

Первый пуш:

```sh
git init
git add .
git commit -m "Add app landing page for GitHub Pages"
git branch -M main
git remote add origin https://github.com/<логин>/<репозиторий>.git
git push -u origin main
```

Пути в проекте относительные, поэтому сайт работает и в подкаталоге (`/<репозиторий>/`), и в корне домена.

Куда именно лягут файлы: если сайт публикуется из **отдельного** репозитория, поменяйте адрес сайта в `canonical`, `og:url`, JSON-LD и `SITE_ROOT` — ссылки на приложение при этом останутся теми же. Если сайт ляжет **в подкаталог** репозитория приложения (например, `website/`), укажите этот путь в `.github/workflows/pages.yml`: `path: website`.

### Если деплой падает

**`Get Pages site failed. Please verify that the repository has Pages enabled and configured to build using GitHub Actions`**
(или `HttpError: Not Found` на `GET /repos/<владелец>/<репозиторий>/pages`) — у репозитория просто не
включён Pages, поэтому `actions/configure-pages` не может прочитать его конфигурацию. Включите Pages по
шагу 2 выше и перезапустите упавший run (**Re-run all jobs**). Самому workflow для этого ничего не нужно.

Включить Pages из workflow можно и без похода в настройки, но только с отдельным токеном: у
`GITHUB_TOKEN` нет прав на создание сайта.

```yaml
      - name: Configure Pages
        uses: actions/configure-pages@v6
        with:
          enablement: true
          token: ${{ secrets.PAGES_TOKEN }}
```

Подойдёт PAT (classic со scope `repo` либо fine-grained с правом `Pages: write`) или токен GitHub App с
`administration: write` и `pages: write` — он кладётся в секрет `PAGES_TOKEN`.

Само предупреждение `Node 20 is being deprecated` к падению отношения не имеет: оно значит, что какая-то
версия экшена ещё собрана под Node 20. В workflow версии подняты до собранных под Node 24 —
`checkout@v7`, `configure-pages@v6`, `upload-pages-artifact@v5`, `deploy-pages@v5`.

### Свой домен

Добавьте файл `CNAME` в корень репозитория с доменом (например, `ose.app`), настройте DNS по инструкции GitHub, затем укажите домен в **Settings → Pages → Custom domain**.

## Мелочи, которые уже сделаны

- Светлая и тёмная тема: следует системной, переключается кнопкой в шапке, выбор запоминается (localStorage).
- Адаптив от 320 px, мобильное меню, `prefers-reduced-motion`.
- Базовая доступность: skip-link, `aria-*`, видимый фокус (3px `secondary` по спеке M3), семантика.
- SEO/соцсети: `description`, Open Graph, Twitter card, JSON-LD `SoftwareApplication`.
- `theme-color` для мобильных браузеров меняется вместе с темой.
