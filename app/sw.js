/* Offline-first service worker for The Hero's Book.
   Bump CACHE_VERSION whenever app files or data change so tablets pick up the update. */

const CACHE_VERSION = 'herosbook-v3';

/* The app shell. Art is deliberately NOT listed here: it is read out of
   player_data.json at install time, so adding a picture to the journal or to a hero
   never means remembering to edit this file too. */
const CORE = [
  './',
  'index.html',
  'css/app.css',
  'js/app.js',
  'data/player_data.json',
  'manifest.webmanifest',
  'icons/icon.svg',
  'icons/icon-192.png',
  'icons/icon-512.png',
  'icons/icon-512-maskable.png'
];

function artUrls(data) {
  const urls = [];
  function push(u) { if (u && urls.indexOf(u) === -1) urls.push(u); }
  (data.heroes || []).forEach(function (h) {
    push(h.banner);
    (h.spells || []).forEach(function (s) { push(s.art); });
    (h.items || []).forEach(function (i) { push(i.art); });
  });
  (data.journal || []).forEach(function (e) { push(e.art); });
  return urls;
}

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(function (cache) {
      return cache.addAll(CORE).then(function () {
        return cache.match('data/player_data.json');
      }).then(function (res) {
        return res ? res.json() : null;
      }).then(function (data) {
        if (!data) return null;
        // One picture failing to cache must not cost the girls offline mode entirely.
        return Promise.all(artUrls(data).map(function (u) {
          return cache.add(u).catch(function () { /* ignore, fetched on demand later */ });
        }));
      });
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k !== CACHE_VERSION; })
        .map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (event) {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    caches.match(event.request).then(function (cached) {
      if (cached) return cached;
      return fetch(event.request).then(function (response) {
        if (response.ok && event.request.url.startsWith(self.location.origin)) {
          const copy = response.clone();
          caches.open(CACHE_VERSION).then(function (cache) { cache.put(event.request, copy); });
        }
        return response;
      });
    })
  );
});
