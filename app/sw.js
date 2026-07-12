/* Offline-first service worker for The Hero's Book.
   Bump CACHE_VERSION whenever app files or data change so tablets pick up the update. */

const CACHE_VERSION = 'herosbook-v2';

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
  'icons/icon-512-maskable.png',
  'art/rainbow_with_clouds_crescent_moon_shield.png',
  'art/sky_saver_meteor_strike.png',
  'art/crescent_moon_shield_spell_card.png',
  'art/meteor_strike_spell_card.png',
  'art/ring_of_sisters_lima_card.png'
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(function (cache) { return cache.addAll(CORE); })
      .then(function () { return self.skipWaiting(); })
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
