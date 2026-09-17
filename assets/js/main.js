/* OSE — лендинг: тема, мобильное меню, состояние шапки, версия из релизов, просмотр скриншотов, год в подвале */
(function () {
  'use strict';

  var root = document.documentElement;
  var STORAGE_KEY = 'ose-theme';
  var header = document.getElementById('header');

  /* ---------- Тема ---------- */

  function storedTheme() {
    try {
      var value = localStorage.getItem(STORAGE_KEY);
      return value === 'light' || value === 'dark' ? value : null;
    } catch (e) {
      return null;
    }
  }

  function systemTheme() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function syncThemeColor(theme) {
    var metas = document.querySelectorAll('meta[name="theme-color"]');
    for (var i = 0; i < metas.length; i++) {
      metas[i].removeAttribute('media');
      metas[i].setAttribute('content', theme === 'dark' ? '#111318' : '#F9F9FF');
    }
  }

  function applyTheme(theme) {
    root.dataset.theme = theme;
    syncThemeColor(theme);
  }

  /* В <head> тема уже могла быть выставлена из localStorage — синхронизируем цвет адресной строки. */
  if (root.dataset.theme === 'dark' || root.dataset.theme === 'light') {
    syncThemeColor(root.dataset.theme);
  }

  var toggle = document.getElementById('theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var next = (storedTheme() || systemTheme()) === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem(STORAGE_KEY, next); } catch (e) {}
      applyTheme(next);
    });
  }

  /* ---------- Мобильное меню ---------- */

  var menuBtn = document.getElementById('menu-toggle');
  var nav = document.getElementById('nav');

  function closeMenu() {
    if (!header) return;
    header.classList.remove('is-open');
    if (menuBtn) menuBtn.setAttribute('aria-expanded', 'false');
  }

  if (header && menuBtn && nav) {
    menuBtn.addEventListener('click', function () {
      var open = header.classList.toggle('is-open');
      menuBtn.setAttribute('aria-expanded', String(open));
    });

    nav.addEventListener('click', function (event) {
      if (event.target.closest('a')) closeMenu();
    });

    document.addEventListener('click', function (event) {
      if (header.classList.contains('is-open') && !header.contains(event.target)) closeMenu();
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') closeMenu();
    });
  }

  /* ---------- Шапка при скролле ---------- */

  if (header) {
    var onScroll = function () {
      header.classList.toggle('is-scrolled', window.scrollY > 8);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ---------- Ripple на кнопках (MD3 press state) ---------- */

  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!reduceMotion) {
    document.addEventListener('pointerdown', function (event) {
      var host = event.target.closest ? event.target.closest('.btn, .icon-btn') : null;
      if (!host) return;

      var rect = host.getBoundingClientRect();
      var size = Math.max(rect.width, rect.height) * 2;
      var ripple = document.createElement('span');

      ripple.className = 'md-ripple';
      ripple.style.width = size + 'px';
      ripple.style.height = size + 'px';
      ripple.style.left = (event.clientX - rect.left - size / 2) + 'px';
      ripple.style.top = (event.clientY - rect.top - size / 2) + 'px';
      ripple.addEventListener('animationend', function () { ripple.remove(); });

      host.appendChild(ripple);
    });
  }

  /* ---------- Год в подвале ---------- */

  var yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  /* ---------- Версия и сборки из последнего релиза приложения ----------
     В разметке стоят значения на момент вёрстки: если запрос не пройдёт (нет сети,
     исчерпан лимит неавторизованных запросов к API), страница останется с ними. */

  var RELEASES_LATEST = 'https://api.github.com/repos/Halantar-git/open-stream-environment/releases/latest';
  var MONTHS = [
    'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
    'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
  ];
  var OS_KEYS = ['windows', 'linux', 'macos'];
  var OS_NAMES = { windows: 'Windows', linux: 'Linux', macos: 'macOS' };
  /* Файлы релиза под каждую систему — в порядке предпочтения */
  var OS_ASSETS = {
    windows: [/-setup\.exe$/i, /\.exe$/i],
    linux: [/\.AppImage$/i, /\.deb$/i],
    macos: [/\.dmg$/i, /-mac\.zip$/i]
  };

  var versionSlots = document.querySelectorAll('[data-release-version]');
  var dateSlots = document.querySelectorAll('[data-release-date]');
  var primaryDownload = document.querySelector('[data-download-primary]');
  var osDownloads = document.querySelectorAll('[data-download-os]');

  if ((versionSlots.length || dateSlots.length || osDownloads.length) && window.fetch) {
    var fill = function (nodes, text) {
      for (var i = 0; i < nodes.length; i++) nodes[i].textContent = text;
    };

    /* Систему смотрим в браузере: в Chromium есть userAgentData, у остальных — строка UA */
    var detectOS = function () {
      var ua = navigator.userAgent || '';
      var platform = navigator.platform || '';
      var data = navigator.userAgentData;

      if (data && data.platform) {
        if (data.platform === 'Windows') return 'windows';
        if (data.platform === 'macOS') return 'macos';
        if (data.platform === 'Linux') return 'linux';
        return '';
      }

      /* iPad в iPadOS 13+ представляется как Macintosh, ChromeOS тянет за Linux —
         но на них не запустить ни один из файлов релиза */
      if (/iPad|iPhone|iPod|Android|CrOS/i.test(ua)) return '';
      if (/Windows/i.test(ua) || /^Win/i.test(platform)) return 'windows';
      if (/Mac OS X|Macintosh/i.test(ua) || /^Mac/i.test(platform)) return 'macos';
      if (/Linux|X11|CrOS/i.test(ua) || /^Linux/i.test(platform)) return 'linux';
      return '';
    };

    var findAsset = function (assets, patterns) {
      for (var p = 0; p < patterns.length; p++) {
        for (var i = 0; i < assets.length; i++) {
          if (patterns[p].test(assets[i].name || '')) return assets[i];
        }
      }
      return null;
    };

    /* Главная кнопка берёт файл у кнопки своей системы: запрос к API для этого не нужен,
       адреса уже лежат в разметке — их подставляет деплой (.github/stamp-release.py) */
    var wirePrimary = function () {
      if (!primaryDownload) return;

      var os = detectOS();
      if (!os) return;

      for (var i = 0; i < osDownloads.length; i++) {
        var link = osDownloads[i];
        if (link.getAttribute('data-download-os') !== os) continue;

        primaryDownload.href = link.href;
        primaryDownload.textContent = 'Скачать для ' + OS_NAMES[os];
        link.hidden = true;
        return;
      }
    };

    wirePrimary();

    /* Освежение поверх деплоя: если запрос прошёл, берём адреса из самого релиза */
    var applyDownloadLinks = function (assets) {
      var i;
      var j;
      var asset;

      for (i = 0; i < OS_KEYS.length; i++) {
        asset = findAsset(assets, OS_ASSETS[OS_KEYS[i]]);
        if (!asset) continue;

        for (j = 0; j < osDownloads.length; j++) {
          if (osDownloads[j].getAttribute('data-download-os') === OS_KEYS[i]) {
            osDownloads[j].href = asset.browser_download_url;
          }
        }
      }

      wirePrimary();
    };

    window.fetch(RELEASES_LATEST, { headers: { accept: 'application/vnd.github+json' } })
      .then(function (response) {
        return response.ok ? response.json() : null;
      })
      .then(function (release) {
        if (!release) return;

        var version = String(release.tag_name || '').replace(/^v/, '');
        var parts = String(release.published_at || '').slice(0, 10).split('-');
        var month = MONTHS[Number(parts[1]) - 1];

        if (version) fill(versionSlots, version);

        /* published_at — UTC; берём дату как есть, без сдвига на часовой пояс */
        if (parts.length === 3 && month) {
          fill(dateSlots, Number(parts[2]) + ' ' + month + ' ' + parts[0]);
        }

        applyDownloadLinks(release.assets || []);

        /* Тот же номер — в разметке для поисковиков */
        var ld = document.querySelector('script[type="application/ld+json"]');
        if (ld && version) {
          try {
            var data = JSON.parse(ld.textContent);
            data.softwareVersion = version;
            ld.textContent = JSON.stringify(data, null, 2);
          } catch (e) {}
        }
      })
      .catch(function () {});
  }

  /* ---------- Просмотр скриншотов ----------
     Ссылки a[data-zoom] ведут на сам файл: без JS картинка просто откроется
     отдельной вкладкой, с JS — поверх страницы, без ухода со сайта. */

  var zoomLinks = document.querySelectorAll('a[data-zoom]');

  if (zoomLinks.length) {
    var box = document.createElement('div');
    var boxImg = document.createElement('img');
    var boxClose = document.createElement('button');
    var trigger = null;

    box.className = 'lightbox';
    box.hidden = true;
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.setAttribute('aria-label', 'Просмотр скриншота');

    boxImg.className = 'lightbox-img';
    boxImg.alt = '';

    boxClose.type = 'button';
    boxClose.className = 'icon-btn lightbox-close';
    boxClose.setAttribute('aria-label', 'Закрыть');
    boxClose.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';

    box.appendChild(boxImg);
    box.appendChild(boxClose);
    document.body.appendChild(box);

    /* Пока открыт просмотр, остальная страница недоступна ни фокусу, ни скроллу */
    var setBackgroundInert = function (on) {
      var nodes = document.body.children;
      for (var i = 0; i < nodes.length; i++) {
        if (nodes[i] !== box) nodes[i].inert = on;
      }
    };

    var openBox = function (link) {
      var thumb = link.querySelector('img');

      boxImg.src = link.getAttribute('href');
      boxImg.alt = thumb ? thumb.alt : '';
      trigger = link;
      box.hidden = false;

      /* Прячем вместе со скроллом и полосу прокрутки — компенсируем её ширину, чтобы страница не дёрнулась */
      var gap = window.innerWidth - root.clientWidth;
      root.style.paddingRight = gap > 0 ? gap + 'px' : '';
      root.classList.add('is-lightbox-open');

      setBackgroundInert(true);
      boxClose.focus();
    };

    var closeBox = function () {
      if (box.hidden) return;

      box.hidden = true;
      setBackgroundInert(false);
      root.classList.remove('is-lightbox-open');
      root.style.paddingRight = '';

      if (trigger) trigger.focus();
      trigger = null;
    };

    for (var i = 0; i < zoomLinks.length; i++) {
      zoomLinks[i].addEventListener('click', function (event) {
        /* Клик с модификатором оставляем браузеру: ссылка ведёт на сам файл */
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        openBox(this);
      });
    }

    /* Клик мимо картинки закрывает */
    box.addEventListener('click', function (event) {
      if (event.target === box) closeBox();
    });

    boxClose.addEventListener('click', closeBox);

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') closeBox();
    });
  }
})();
