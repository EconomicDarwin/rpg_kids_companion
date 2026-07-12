/* The Hero's Book — companion app for the Lima Clan campaign.
   Read-mostly viewer over data/player_data.json (generated from campaign canon).
   Local-only state per tablet: chosen hero, damage taken. No servers, no accounts. */

(function () {
  'use strict';

  const LS_HERO = 'herosbook.heroId';
  const LS_DAMAGE = 'herosbook.damage.'; // + heroId
  const MAX_DAMAGE = 3; // Hero Kids track: Bruised, Hurt, KO
  const HEALTH_LABELS = ['Ready to go!', 'Bruised', 'Hurt', 'Knocked out. Time for a rest!'];

  let DATA = null;
  let currentTab = 'hero';

  const view = document.getElementById('view');
  const tabbar = document.getElementById('tabbar');

  // ---------- Tiny helpers ----------

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function getHeroId() { return localStorage.getItem(LS_HERO); }
  function setHeroId(id) { localStorage.setItem(LS_HERO, id); }

  function getDamage(heroId) {
    const n = parseInt(localStorage.getItem(LS_DAMAGE + heroId), 10);
    return Number.isInteger(n) ? Math.min(Math.max(n, 0), MAX_DAMAGE) : 0;
  }

  function setDamage(heroId, n) {
    localStorage.setItem(LS_DAMAGE + heroId, String(n));
  }

  function heroById(id) {
    return DATA.heroes.find(function (h) { return h.id === id; }) || null;
  }

  function setAccent(color) {
    document.documentElement.style.setProperty('--accent-c', color || '#8b5cf6');
  }

  function canSpeak() { return 'speechSynthesis' in window; }

  function speak(text) {
    if (!canSpeak()) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 0.9;
    window.speechSynthesis.speak(u);
  }

  function speakButton(text) {
    if (!canSpeak()) return null;
    const btn = el('button', 'speak-btn', '🔊');
    btn.setAttribute('aria-label', 'Read this out loud');
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      speak(text);
    });
    return btn;
  }

  function lightbox(src, alt) {
    const box = document.getElementById('art-lightbox');
    const img = document.getElementById('art-lightbox-img');
    img.src = src;
    img.alt = alt || 'Card art';
    box.hidden = false;
  }

  // ---------- Shared card renderer ----------

  function kcard(entry, opts) {
    opts = opts || {};
    const card = el('div', 'kcard');
    if (entry.icon) card.appendChild(el('span', 'kcard-icon', entry.icon));

    const body = el('div');
    body.style.flex = '1';
    body.appendChild(el('div', 'kcard-name', entry.name));
    if (entry.type) body.appendChild(el('div', 'kcard-type', entry.type));
    if (entry.text) body.appendChild(el('div', 'kcard-text', entry.text));
    if (entry.limit) body.appendChild(el('div', 'kcard-limit', entry.limit));
    card.appendChild(body);

    const sayText = entry.name + '. ' + (entry.text || '') + ' ' + (entry.limit || '');
    const sb = speakButton(sayText);
    if (sb) card.appendChild(sb);

    if (entry.art && !opts.noArt) {
      const art = el('img', 'kcard-art');
      art.src = entry.art;
      art.alt = entry.name + ' card art. Tap to see it big.';
      art.addEventListener('click', function () { lightbox(entry.art, entry.name); });
      card.appendChild(art);
    }
    return card;
  }

  function sectionHeader(icon, text) {
    const h = el('h2', 'section-h');
    h.appendChild(el('span', '', icon));
    h.appendChild(el('span', '', text));
    return h;
  }

  // ---------- Screens ----------

  function renderPicker() {
    tabbar.hidden = true;
    setAccent(null);
    view.innerHTML = '';
    view.appendChild(el('p', 'picker-hello', 'Hello, hero! 🌟'));
    view.appendChild(el('p', 'picker-sub', 'Tap your hero to open your book.'));

    const grid = el('div', 'picker-grid');
    DATA.heroes.forEach(function (h) {
      const btn = el('button', 'picker-card');
      btn.style.setProperty('--accent-c', h.accent);
      if (h.banner) {
        const img = el('img');
        img.src = h.banner;
        img.alt = h.name;
        btn.appendChild(img);
      } else {
        btn.appendChild(el('div', 'picker-splat', '🛡️'));
      }
      const body = el('div');
      body.appendChild(el('div', 'picker-name', h.name));
      body.appendChild(el('div', 'picker-class', h.class + (h.joined ? '' : ' · joining soon!')));
      btn.appendChild(body);
      btn.addEventListener('click', function () {
        setHeroId(h.id);
        currentTab = 'hero';
        renderApp();
      });
      grid.appendChild(btn);
    });
    view.appendChild(grid);
  }

  function renderHealth(hero, container) {
    container.appendChild(sectionHeader('💖', 'My Hearts'));
    const damage = getDamage(hero.id);

    const row = el('div', 'health-row');
    for (let i = 0; i < MAX_DAMAGE; i++) {
      const full = i < MAX_DAMAGE - damage;
      const btn = el('button', 'heart-btn' + (full ? '' : ' empty'), full ? '❤️' : '💔');
      btn.setAttribute('aria-label', full ? 'Full heart. Tap if you get hurt.' : 'Lost heart. Tap when you are healed.');
      btn.addEventListener('click', function () {
        const d = getDamage(hero.id);
        // Tapping a full heart takes damage, tapping a broken one heals.
        setDamage(hero.id, full ? Math.min(d + 1, MAX_DAMAGE) : Math.max(d - 1, 0));
        renderApp();
      });
      row.appendChild(btn);
    }
    container.appendChild(row);

    const label = el('div', 'health-label' + (damage >= MAX_DAMAGE ? ' ko' : ''), HEALTH_LABELS[damage]);
    container.appendChild(label);
    container.appendChild(el('div', 'health-hint', 'Tap a heart when you get hurt. Tap it again when you are healed.'));
  }

  function renderStats(hero, container) {
    container.appendChild(sectionHeader('🎲', 'My Dice'));
    const row = el('div', 'stat-row');
    const stats = [
      { key: 'melee', icon: '⚔️', name: 'Melee' },
      { key: 'ranged', icon: '🏹', name: 'Ranged' },
      { key: 'magic', icon: '✨', name: 'Magic' },
      { key: 'armor', icon: '🛡️', name: 'Armor' }
    ];
    stats.forEach(function (s) {
      const n = hero.stats[s.key] || 0;
      const chip = el('div', 'stat-chip');
      chip.appendChild(el('span', 'stat-icon', s.icon));
      chip.appendChild(el('span', 'stat-name', s.name));
      chip.appendChild(el('span', 'stat-dice' + (n ? '' : ' none'), n ? '🎲'.repeat(n) : '—'));
      row.appendChild(chip);
    });
    container.appendChild(row);
  }

  function renderHeroScreen() {
    const hero = heroById(getHeroId());
    if (!hero) { renderPicker(); return; }
    setAccent(hero.accent);
    view.innerHTML = '';

    const banner = el('div', 'hero-banner');
    banner.style.setProperty('--accent-c', hero.accent);
    if (hero.banner) {
      const img = el('img');
      img.src = hero.banner;
      img.alt = hero.name;
      banner.appendChild(img);
    }
    const nameBox = el('div', 'hero-name', hero.name);
    nameBox.appendChild(el('span', 'hero-class', hero.class));
    banner.appendChild(nameBox);
    view.appendChild(banner);
    view.appendChild(el('p', 'hero-tagline', hero.tagline));

    renderHealth(hero, view);
    renderStats(hero, view);

    view.appendChild(sectionHeader('⭐', 'My Powers'));
    const abilities = el('div', 'card-list');
    hero.abilities.forEach(function (a) { abilities.appendChild(kcard(a)); });
    view.appendChild(abilities);

    if (hero.spells.length) {
      view.appendChild(sectionHeader('🌟', 'My Spells'));
      const spells = el('div', 'card-list');
      hero.spells.forEach(function (s) { spells.appendChild(kcard(s)); });
      view.appendChild(spells);
    }

    if (hero.items.length) {
      view.appendChild(sectionHeader('🎒', 'My Things'));
      const items = el('div', 'card-list');
      hero.items.forEach(function (i) { items.appendChild(kcard(i)); });
      view.appendChild(items);
    }
  }

  function renderFamilyScreen() {
    view.innerHTML = '';
    const title = el('h1', 'screen-title');
    title.appendChild(el('span', '', '👧'));
    title.appendChild(el('span', '', 'The Lima Sisters'));
    view.appendChild(title);

    const myId = getHeroId();
    DATA.heroes.filter(function (h) { return h.id !== myId; }).forEach(function (h) {
      view.appendChild(sectionHeader('🦸', ''));
      const head = view.lastChild;
      head.lastChild.textContent = h.name;
      if (!h.joined) head.appendChild(el('span', 'badge-soon', 'joining soon!'));

      if (h.banner) {
        const banner = el('div', 'hero-banner family-card');
        banner.style.setProperty('--accent-c', h.accent);
        const img = el('img');
        img.src = h.banner;
        img.alt = h.name;
        banner.appendChild(img);
        view.appendChild(banner);
      }
      view.appendChild(el('p', 'hero-tagline', h.tagline));

      const list = el('div', 'card-list');
      h.abilities.forEach(function (a) {
        const c = kcard(a);
        c.style.setProperty('--accent-c', h.accent);
        list.appendChild(c);
      });
      h.spells.forEach(function (s) {
        const c = kcard(s);
        c.style.setProperty('--accent-c', h.accent);
        list.appendChild(c);
      });
      view.appendChild(list);
    });
  }

  function renderPetsScreen() {
    view.innerHTML = '';
    const box = el('div', 'pets-empty');
    box.appendChild(el('span', 'pets-icon', '🐾'));
    box.appendChild(el('p', '', DATA.pets.text));
    view.appendChild(box);
  }

  function renderTreasureScreen() {
    view.innerHTML = '';
    const title = el('h1', 'screen-title');
    title.appendChild(el('span', '', '💰'));
    title.appendChild(el('span', '', 'Our Treasure'));
    view.appendChild(title);

    const gold = el('div', 'gold-card');
    gold.appendChild(el('span', 'gold-icon', '🪙'));
    const gbody = el('div');
    gbody.appendChild(el('div', 'gold-amount', DATA.party.gold === null ? '?' : String(DATA.party.gold) + ' gold'));
    if (DATA.party.goldNote) gbody.appendChild(el('div', 'gold-note', DATA.party.goldNote));
    gold.appendChild(gbody);
    view.appendChild(gold);

    view.appendChild(sectionHeader('🎒', 'Things We Share'));
    const shared = el('div', 'card-list');
    DATA.party.sharedItems.forEach(function (i) { shared.appendChild(kcard(i)); });
    view.appendChild(shared);

    const hero = heroById(getHeroId());
    if (hero && hero.items.length) {
      view.appendChild(sectionHeader('💍', 'My Things'));
      const mine = el('div', 'card-list');
      hero.items.forEach(function (i) { mine.appendChild(kcard(i)); });
      view.appendChild(mine);
    }
  }

  function renderStoryScreen() {
    view.innerHTML = '';
    const title = el('h1', 'screen-title');
    title.appendChild(el('span', '', '📖'));
    title.appendChild(el('span', '', 'Our Story So Far'));
    view.appendChild(title);

    const list = el('div', 'card-list');
    DATA.journal.slice().reverse().forEach(function (entry) {
      const card = el('div', 'kcard journal-card');
      const head = el('div', 'journal-head');
      head.appendChild(el('span', 'journal-session', 'Game ' + entry.session));
      head.appendChild(el('span', 'journal-title', entry.title));
      const sb = speakButton(entry.title + '. ' + entry.text);
      if (sb) head.appendChild(sb);
      card.appendChild(head);
      card.appendChild(el('p', 'journal-text', entry.text));
      list.appendChild(card);
    });
    view.appendChild(list);

    view.appendChild(sectionHeader('🗡️', 'Our Quests'));
    const quests = el('div', 'card-list');
    DATA.quests.forEach(function (q) { quests.appendChild(kcard(q)); });
    view.appendChild(quests);
  }

  // ---------- Navigation ----------

  const SCREENS = {
    hero: renderHeroScreen,
    family: renderFamilyScreen,
    pets: renderPetsScreen,
    treasure: renderTreasureScreen,
    story: renderStoryScreen
  };

  function renderApp() {
    if (!getHeroId() || !heroById(getHeroId())) { renderPicker(); return; }
    tabbar.hidden = false;
    setAccent(heroById(getHeroId()).accent);
    document.querySelectorAll('.tab').forEach(function (t) {
      t.classList.toggle('active', t.dataset.tab === currentTab);
    });
    SCREENS[currentTab]();
    view.scrollTop = 0;
  }

  tabbar.addEventListener('click', function (e) {
    const tab = e.target.closest('.tab');
    if (!tab) return;
    currentTab = tab.dataset.tab;
    renderApp();
  });

  // ---------- Grown-up corner (press and hold the gear) ----------

  (function grownUpCorner() {
    const btn = document.getElementById('grownup-btn');
    const panel = document.getElementById('grownup-panel');
    let timer = null;

    function open() { panel.hidden = false; }

    btn.addEventListener('pointerdown', function () {
      timer = setTimeout(open, 1200);
    });
    ['pointerup', 'pointerleave', 'pointercancel'].forEach(function (evt) {
      btn.addEventListener(evt, function () { clearTimeout(timer); });
    });

    document.getElementById('ga-close').addEventListener('click', function () { panel.hidden = true; });

    document.getElementById('ga-reset-health').addEventListener('click', function () {
      DATA.heroes.forEach(function (h) { setDamage(h.id, 0); });
      panel.hidden = true;
      renderApp();
    });

    document.getElementById('ga-switch-hero').addEventListener('click', function () {
      localStorage.removeItem(LS_HERO);
      panel.hidden = true;
      renderPicker();
    });

    document.getElementById('ga-reload').addEventListener('click', function () {
      if ('caches' in window) {
        caches.keys().then(function (keys) {
          return Promise.all(keys.map(function (k) { return caches.delete(k); }));
        }).then(function () { location.reload(); });
      } else {
        location.reload();
      }
    });
  })();

  document.getElementById('art-lightbox-close').addEventListener('click', function () {
    document.getElementById('art-lightbox').hidden = true;
  });
  document.getElementById('art-lightbox').addEventListener('click', function (e) {
    if (e.target === e.currentTarget) e.currentTarget.hidden = true;
  });

  // ---------- Boot ----------

  fetch('data/player_data.json')
    .then(function (r) { return r.json(); })
    .then(function (data) {
      DATA = data;
      // Setup helper: ?hero=<id>&tab=<name> preselects for this tablet (useful for first-time bookmarks).
      const params = new URLSearchParams(location.search);
      if (params.get('hero') && heroById(params.get('hero'))) setHeroId(params.get('hero'));
      if (params.get('tab') && SCREENS[params.get('tab')]) currentTab = params.get('tab');
      renderApp();
    })
    .catch(function () {
      view.innerHTML = '';
      const oops = el('div', 'pets-empty');
      oops.appendChild(el('span', 'pets-icon', '🌧️'));
      oops.appendChild(el('p', '', 'Oh no, the book could not open. Ask a grown-up to check the tablet.'));
      view.appendChild(oops);
    });

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(function () { /* offline caching is a bonus, not required */ });
  }
})();
