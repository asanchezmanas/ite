// service-worker.js
const CACHE_VERSION = 'v1.0.0';
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const API_CACHE = `api-${CACHE_VERSION}`;
const MAP_CACHE = `map-${CACHE_VERSION}`;

// Assets to precache
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/css/style.css',
  '/css/map.css',
  '/js/app.js',
  '/manifest.json',
  '/assets/icon-192.png',
  '/assets/icon-512.png',
  // Add all your JS modules here
  '/js/core/router.js',
  '/js/core/store.js',
  '/js/core/api.js',
  '/js/core/auth.js',
  '/js/pages/home.js',
  '/js/pages/login.js',
  '/js/pages/tracking.js',
  '/js/pages/map.js',
  '/js/pages/post-activity.js',
  '/js/services/location.js',
  '/js/services/map.js'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
      .catch(error => {
        console.error('Error caching assets:', error);
      })
  );
});

// Activate event - cleanup old caches
self.addEventListener('activate', event => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames
            .filter(name => {
              // Delete old caches
              return name !== STATIC_CACHE && 
                     name !== API_CACHE && 
                     name !== MAP_CACHE;
            })
            .map(name => {
              console.log('Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // API requests - network first, then cache
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request, API_CACHE));
  }
  // Map tiles - cache first
  else if (url.hostname.includes('tile.openstreetmap.org')) {
    event.respondWith(cacheFirst(request, MAP_CACHE));
  }
  // Static assets - cache first
  else {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
  }
});

// Strategy: Cache first, fallback to network
async function cacheFirst(request, cacheName) {
  try {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    
    if (cached) {
      // Return cached version
      return cached;
    }
    
    // Fetch from network
    const response = await fetch(request);
    
    // Cache the response
    if (response.ok) {
      cache.put(request, response.clone());
    }
    
    return response;
    
  } catch (error) {
    console.error('Cache first error:', error);
    
    // Return offline fallback
    return new Response('Offline', {
      status: 503,
      statusText: 'Service Unavailable'
    });
  }
}

// Strategy: Network first, fallback to cache
async function networkFirst(request, cacheName) {
  try {
    // Try network first
    const response = await fetch(request);
    
    // Cache successful responses
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    
    return response;
    
  } catch (error) {
    console.log('Network failed, trying cache...');
    
    // Fallback to cache
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    
    if (cached) {
      return cached;
    }
    
    // Return offline response
    return new Response(
      JSON.stringify({ error: 'Offline' }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// Push notification
self.addEventListener('push', event => {
  console.log('Push received:', event);
  
  const data = event.data ? event.data.json() : {};
  
  const options = {
    body: data.body || 'Nueva notificación',
    icon: '/assets/icon-192.png',
    badge: '/assets/icon-96.png',
    vibrate: [200, 100, 200],
    data: data.data || {},
    actions: data.actions || []
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'Territory Conquest', options)
  );
});

// Notification click
self.addEventListener('notificationclick', event => {
  console.log('Notification clicked:', event);
  
  event.notification.close();
  
  const urlToOpen = event.notification.data.url || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(clientList => {
        // If window is already open, focus it
        for (const client of clientList) {
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }
        
        // Otherwise, open new window
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Background sync (offline activities)
self.addEventListener('sync', event => {
  console.log('Background sync:', event.tag);
  
  if (event.tag === 'sync-activities') {
    event.waitUntil(syncPendingActivities());
  }
});

async function syncPendingActivities() {
  try {
    // Get pending activities from IndexedDB
    // Send to server
    // Clear from queue
    console.log('Syncing pending activities...');
  } catch (error) {
    console.error('Sync failed:', error);
  }
}
