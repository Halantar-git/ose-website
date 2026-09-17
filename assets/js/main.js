/* OSE — лендинг: тема, мобильное меню, состояние шапки, год в подвале */
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
})();
