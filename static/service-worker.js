/*
FeedSafe service worker
========================
This is what makes the installed app keep working with no internet
connection. The browser runs this file in the background, separate
from the page itself.

Strategy, kept deliberately simple for a small, mostly-static app:
  - On install, pre-download ("precache") everything the app needs
    to run standalone: the page shell, the manifest, the icons, and
    the full medication list from /api/medications.
  - On every later visit, serve those files straight from the cache
    first — instantly, and even with the phone in airplane mode —
    then quietly refresh the cache in the background if a network
    connection is available (so updates still reach the phone).
*/

const CACHE_NAME = "feedsafe-cache-v1";

const PRECACHE_URLS = [
  "/",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/api/medications",
];

// --- INSTALL: runs once, the first time the service worker is registered ---
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS))
  );
});

// --- ACTIVATE: clears out any old cache version from a previous update ---
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );
});

// --- FETCH: intercepts every network request the page makes ---
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      // Serve from cache immediately if we have it.
      if (cachedResponse) {
        return cachedResponse;
      }

      // Otherwise, try the network, and cache a copy for next time.
      return fetch(event.request)
        .then((networkResponse) => {
          return caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, networkResponse.clone());
            return networkResponse;
          });
        })
        .catch(() => {
          // No cache, no network — nothing we can do for this request.
          return new Response("Offline and not cached yet.", { status: 503 });
        });
    })
  );
});
