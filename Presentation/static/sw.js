const CACHE = 'zbor-app-shell-v3';
const APP_SHELL = [
  '/static/styles.css?v=8',
  '/static/refinements.css?v=2',
  '/static/hotfix.css?v=2',
  '/static/app.js?v=7',
  '/static/push.js?v=1',
  '/static/icons/icon.svg',
  '/static/offline.html',
  '/manifest.webmanifest'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('push', event => {
  let data = {};
  try { data = event.data?.json() || {}; } catch { /* Invalid payload: show a generic notice. */ }
  const title = typeof data.title === 'string' ? data.title : 'Upravljanje zbora';
  const body = typeof data.body === 'string' ? data.body : 'Novost v aplikaciji.';
  const url = typeof data.url === 'string' && data.url.startsWith('/') && !data.url.startsWith('//') ? data.url : '/dogodki';
  event.waitUntil(self.registration.showNotification(title, {
    body,
    icon: '/static/icons/icon.svg',
    badge: '/static/icons/icon.svg',
    tag: typeof data.tag === 'string' ? data.tag : 'zbor-dogodek',
    data: { url }
  }));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const target = new URL(event.notification.data?.url || '/dogodki', self.location.origin);
  if (target.origin !== self.location.origin) return;
  event.waitUntil((async () => {
    const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    const open = windows.find(client => new URL(client.url).pathname === target.pathname);
    if (open) { await open.focus(); return; }
    await self.clients.openWindow(target.href);
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin) return;
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => caches.match('/static/offline.html')));
    return;
  }
  if (url.pathname.startsWith('/static/') || url.pathname === '/manifest.webmanifest') {
    event.respondWith(caches.match(request).then(cached => cached || fetch(request).then(response => {
      if (response.ok) caches.open(CACHE).then(cache => cache.put(request, response.clone()));
      return response;
    })));
  }
});
