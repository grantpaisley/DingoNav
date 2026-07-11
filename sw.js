// DingoNav service worker — cache-first so the app works fully offline.
// Bump CACHE when shipping a new version.
const CACHE = 'dingonav-v2';
const SHELL = [
  './', './index.html', './manifest.json', './icon-192.png', './icon-512.png',
  './vendor/maplibre-gl.js', './vendor/maplibre-gl.css', './vendor/pmtiles.js', './vendor/fflate.js',
  './basemap/layers.json',
  './basemap/sprites/dark.json', './basemap/sprites/dark.png',
  './basemap/sprites/dark@2x.json', './basemap/sprites/dark@2x.png',
];
const FONTS = ['Noto Sans Regular', 'Noto Sans Medium', 'Noto Sans Italic'];
const RANGES = ['0-255', '256-511', '512-767'];
for (const f of FONTS) for (const r of RANGES) SHELL.push(`./basemap/fonts/${encodeURIComponent(f)}/${r}.pbf`);

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET' || !e.request.url.startsWith(self.location.origin)) return;
  // the .pmtiles basemap is stored in IndexedDB by the app, not the SW cache
  if (e.request.url.endsWith('.pmtiles')) return;
  const path = new URL(e.request.url).pathname;
  const isShellEntry = e.request.mode === 'navigate' || path.endsWith('/index.html') || path.endsWith('/sw.js');
  if (isShellEntry) {
    // network-first: pick up new app versions when online, cached shell when offline
    e.respondWith(fetch(e.request).then(resp => {
      if (resp.ok) { const copy = resp.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
      return resp;
    }).catch(() => caches.match(e.request, { ignoreSearch: true }).then(hit => hit || caches.match('./index.html'))));
    return;
  }
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then(hit => hit || fetch(e.request).then(resp => {
      if (resp.ok) { const copy = resp.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
      return resp;
    }).catch(() => hit))
  );
});
