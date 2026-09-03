/* Repeat-visit cache for same-origin images and fonts only. HTML, styles and
   scripts stay on the normal HTTP cache path to avoid mismatched deployments. */
const STATIC_CACHE = 'azure-mastery-static-v1';
const STATIC_DESTINATIONS = new Set(['image', 'font']);

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(key => key.startsWith('azure-mastery-static-') && key !== STATIC_CACHE)
          .map(key => caches.delete(key))
      ))
      .catch(() => undefined)
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (
    request.method !== 'GET' ||
    !STATIC_DESTINATIONS.has(request.destination) ||
    new URL(request.url).origin !== self.location.origin
  ) {
    return;
  }

  event.respondWith(
    caches.open(STATIC_CACHE).then(async cache => {
      const cached = await cache.match(request).catch(() => undefined);
      const refresh = fetch(request).then(async response => {
        if (response.ok && response.type === 'basic') {
          try { await cache.put(request, response.clone()); } catch (_) { /* storage is optional */ }
        }
        return response;
      });

      if (cached) {
        event.waitUntil(refresh.catch(() => undefined));
        return cached;
      }

      return refresh;
    }, () => fetch(request))
  );
});
