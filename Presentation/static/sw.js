const CACHE = 'zbor-app-shell-v8';
const APP_SHELL = [
  '/static/styles.css?v=9',
  '/static/refinements.css?v=4',
  '/static/hotfix.css?v=6',
  '/static/app.js?v=14',
  '/static/push.js?v=2',
  '/static/icons/icon.svg',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/apple-touch-icon.png',
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
    icon: '/static/icons/icon-192.png',
    badge: '/static/icons/icon-192.png',
    tag: typeof data.tag === 'string' ? data.tag : 'zbor-dogodek',
    actions: Array.isArray(data.actions) ? data.actions.filter(item => ['present','absent'].includes(item.action)).slice(0, 2) : [],
    data: { url, eventId: data.event_id }
  }));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const target = new URL(event.notification.data?.url || '/dogodki', self.location.origin);
  if (target.origin !== self.location.origin) return;
  event.waitUntil((async () => {
    if (['present','absent'].includes(event.action) && Number.isInteger(event.notification.data?.eventId)) {
      try {
        const result = await fetch('/api/prisotnost', {method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json'}, body:JSON.stringify({event_id:event.notification.data.eventId, status:event.action})});
        if (result.ok && result.headers.get('content-type')?.includes('application/json')) {
          await self.registration.showNotification('Prisotnost je shranjena', {body:event.action === 'present' ? 'Prisoten' : 'Odsoten', data:{url:target.pathname}, tag:'attendance-saved'});
          return;
        }
      } catch { /* Offline or expired session: continue on the event page. */ }
      target.searchParams.set('attendance', event.action);
    }
    if (!event.action && Number.isInteger(event.notification.data?.eventId)) {
      target.searchParams.set('attendance', 'choose');
    }
    const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    const open = windows.find(client => new URL(client.url).pathname === target.pathname);
    if (open) { await open.navigate(target.href); await open.focus(); return; }
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
