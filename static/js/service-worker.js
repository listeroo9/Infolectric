const CACHE_NAME = 'infolectric-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/static/manifest.json',
    '/static/images/Apps_logo1.png',
    '/static/images/Apps_logo.png',
    '/static/images/logo3.png',
    '/static/images/background.png',
    '/service-worker.js'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(ASSETS_TO_CACHE))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET') {
        return;
    }

    const requestUrl = new URL(event.request.url);
    const isSameOrigin = requestUrl.origin === location.origin;

    if (isSameOrigin && requestUrl.pathname.startsWith('/static/')) {
        event.respondWith(cacheFirst(event.request));
        return;
    }

    if (isSameOrigin && (requestUrl.pathname === '/' || requestUrl.pathname.endsWith('.html') || requestUrl.pathname === '/profile/' || requestUrl.pathname === '/login/' || requestUrl.pathname === '/register/')) {
        event.respondWith(networkFirst(event.request));
        return;
    }

    event.respondWith(networkFirst(event.request));
});

function cacheFirst(request) {
    return caches.match(request).then(cachedResponse => {
        if (cachedResponse) {
            return cachedResponse;
        }
        return fetch(request).then(networkResponse => {
            return caches.open(CACHE_NAME).then(cache => {
                cache.put(request, networkResponse.clone());
                return networkResponse;
            });
        }).catch(() => {
            return caches.match('/');
        });
    });
}

function networkFirst(request) {
    return caches.open(CACHE_NAME).then(cache => {
        return fetch(request)
            .then(networkResponse => {
                if (networkResponse && networkResponse.status === 200) {
                    cache.put(request, networkResponse.clone());
                }
                return networkResponse;
            })
            .catch(() => caches.match(request).then(cachedResponse => cachedResponse || caches.match('/')));
    });
}
