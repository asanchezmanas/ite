---

## ⚡ Optimizaciones de Performance

### 1. Lazy Loading de Componentes
```javascript
/**
 * Cargar componentes solo cuando se necesitan
 */

class ComponentLoader {
  static cache = new Map();
  
  static async load(componentPath) {
    // Check cache
    if (this.cache.has(componentPath)) {
      return this.cache.get(componentPath);
    }
    
    // Dynamic import
    const module = await import(componentPath);
    const Component = module.default;
    
    // Cache
    this.cache.set(componentPath, Component);
    
    return Component;
  }
}

// Uso en Router
Router.route('/map', async () => {
  const MapPage = await ComponentLoader.load('./pages/MapPage.js');
  return new MapPage();
});
```

### 2. Virtual Scrolling para Listas
```javascript
/**
 * Renderizar solo elementos visibles en listas largas
 */

class VirtualList {
  constructor(container, items, itemHeight, renderItem) {
    this.container = container;
    this.items = items;
    this.itemHeight = itemHeight;
    this.renderItem = renderItem;
    
    this.visibleStart = 0;
    this.visibleEnd = 0;
    
    this.init();
  }
  
  init() {
    // Calculate visible range
    this.updateVisibleRange();
    
    // Render visible items
    this.render();
    
    // Scroll listener
    this.container.addEventListener('scroll', () => {
      this.updateVisibleRange();
      this.render();
    });
  }
  
  updateVisibleRange() {
    const scrollTop = this.container.scrollTop;
    const containerHeight = this.container.clientHeight;
    
    this.visibleStart = Math.floor(scrollTop / this.itemHeight);
    this.visibleEnd = Math.ceil((scrollTop + containerHeight) / this.itemHeight);
    
    // Add buffer
    this.visibleStart = Math.max(0, this.visibleStart - 5);
    this.visibleEnd = Math.min(this.items.length, this.visibleEnd + 5);
  }
  
  render() {
    // Clear
    this.container.innerHTML = '';
    
    // Create spacer for scroll height
    const totalHeight = this.items.length * this.itemHeight;
    const spacer = document.createElement('div');
    spacer.style.height = `${totalHeight}px`;
    spacer.style.position = 'relative';
    
    // Render visible items
    for (let i = this.visibleStart; i < this.visibleEnd; i++) {
      const item = this.items[i];
      const element = this.renderItem(item, i);
      element.style.position = 'absolute';
      element.style.top = `${i * this.itemHeight}px`;
      element.style.height = `${this.itemHeight}px`;
      spacer.appendChild(element);
    }
    
    this.container.appendChild(spacer);
  }
}

// Uso en RankingsPage
const virtualList = new VirtualList(
  container,
  rankings, // 10,000 items
  80, // height per item
  (ranking, index) => {
    return createRankingCard(ranking);
  }
);
```

### 3. Debounce y Throttle
```javascript
/**
 * Optimizar eventos frecuentes
 */

// Debounce - Ejecutar después de que termine la acción
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Throttle - Ejecutar máximo cada X ms
function throttle(func, limit) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// Uso
const searchInput = document.querySelector('#search');
searchInput.addEventListener('input', debounce((e) => {
  performSearch(e.target.value);
}, 300));

// Scroll tracking
window.addEventListener('scroll', throttle(() => {
  updateScrollPosition();
}, 100));
```

### 4. Image Lazy Loading
```javascript
/**
 * Cargar imágenes solo cuando sean visibles
 */

class LazyImageLoader {
  constructor() {
    this.observer = new IntersectionObserver(
      (entries) => this.handleIntersection(entries),
      {
        rootMargin: '50px' // Load 50px before visible
      }
    );
  }
  
  observe(img) {
    this.observer.observe(img);
  }
  
  handleIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        const src = img.dataset.src;
        
        if (src) {
          img.src = src;
          img.removeAttribute('data-src');
          this.observer.unobserve(img);
        }
      }
    });
  }
}

// HTML
// <img data-src="/path/to/image.jpg" alt="..." class="lazy">

// Inicializar
const lazyLoader = new LazyImageLoader();
document.querySelectorAll('img.lazy').forEach(img => {
  lazyLoader.observe(img);
});
```

### 5. Request Batching
```javascript
/**
 * Agrupar múltiples requests en uno
 */

class RequestBatcher {
  constructor(batchFunction, wait = 50) {
    this.batchFunction = batchFunction;
    this.wait = wait;
    this.queue = [];
    this.timeout = null;
  }
  
  add(request) {
    return new Promise((resolve, reject) => {
      this.queue.push({ request, resolve, reject });
      
      if (this.timeout) {
        clearTimeout(this.timeout);
      }
      
      this.timeout = setTimeout(() => {
        this.flush();
      }, this.wait);
    });
  }
  
  async flush() {
    if (this.queue.length === 0) return;
    
    const batch = this.queue.splice(0);
    const requests = batch.map(item => item.request);
    
    try {
      const results = await this.batchFunction(requests);
      
      batch.forEach((item, index) => {
        item.resolve(results[index]);
      });
    } catch (error) {
      batch.forEach(item => {
        item.reject(error);
      });
    }
  }
}

// Uso
const territoryBatcher = new RequestBatcher(async (territoryIds) => {
  return API.risk.getTerritories(territoryIds);
});

// Múltiples llamadas se agrupan automáticamente
const territory1 = await territoryBatcher.add('id1');
const territory2 = await territoryBatcher.add('id2');
const territory3 = await territoryBatcher.add('id3');
// Solo 1 request al backend con [id1, id2, id3]
```

### 6. Memory Management
```javascript
/**
 * Gestión de memoria para evitar leaks
 */

class Component {
  constructor() {
    this.listeners = [];
    this.timers = [];
  }
  
  addEventListener(element, event, handler) {
    element.addEventListener(event, handler);
    this.listeners.push({ element, event, handler });
  }
  
  setTimeout(callback, delay) {
    const id = setTimeout(callback, delay);
    this.timers.push(id);
    return id;
  }
  
  setInterval(callback, interval) {
    const id = setInterval(callback, interval);
    this.timers.push(id);
    return id;
  }
  
  destroy() {
    // Remove all event listeners
    this.listeners.forEach(({ element, event, handler }) => {
      element.removeEventListener(event, handler);
    });
    this.listeners = [];
    
    // Clear all timers
    this.timers.forEach(id => {
      clearTimeout(id);
      clearInterval(id);
    });
    this.timers = [];
    
    // Remove DOM elements
    if (this.element && this.element.parentNode) {
      this.element.parentNode.removeChild(this.element);
    }
  }
}
```

---

## 🎭 Animaciones y Transiciones

### Animaciones CSS
```css
/* animations.css */

/* Page transitions */
@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideOutLeft {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(-100%);
    opacity: 0;
  }
}

/* Battle pulse */
@keyframes battlePulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.5);
    opacity: 0;
  }
}

.battle-pulse {
  animation: battlePulse 2s infinite;
}

/* Conquest celebration */
@keyframes conquestCelebration {
  0% {
    transform: scale(0.5) rotate(0deg);
    opacity: 0;
  }
  50% {
    transform: scale(1.2) rotate(180deg);
    opacity: 1;
  }
  100% {
    transform: scale(1) rotate(360deg);
    opacity: 1;
  }
}

/* Loading spinner */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.spinner {
  animation: spin 1s linear infinite;
}

/* Slide up toast */
@keyframes slideUp {
  from {
    transform: translateY(100px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Shimmer loading */
@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

.skeleton {
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 1000px 100%;
  animation: shimmer 2s infinite;
}
```

### Animaciones JavaScript
```javascript
/**
 * Animaciones programáticas
 */

class Animator {
  // Smooth number animation
  static animateNumber(element, start, end, duration) {
    const startTime = performance.now();
    
    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function (easeOutQuad)
      const eased = 1 - (1 - progress) * (1 - progress);
      
      const current = start + (end - start) * eased;
      element.textContent = Math.round(current);
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    
    requestAnimationFrame(animate);
  }
  
  // Shake animation
  static shake(element) {
    element.style.animation = 'none';
    setTimeout(() => {
      element.style.animation = 'shake 0.5s';
    }, 10);
  }
  
  // Confetti on conquest
  static confetti(container) {
    const confettiCount = 50;
    const colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF'];
    
    for (let i = 0; i < confettiCount; i++) {
      const confetti = document.createElement('div');
      confetti.className = 'confetti';
      confetti.style.left = Math.random() * 100 + '%';
      confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
      confetti.style.animationDelay = Math.random() * 3 + 's';
      
      container.appendChild(confetti);
      
      setTimeout(() => confetti.remove(), 3000);
    }
  }
}
```

---

## 🔐 Seguridad

### 1. XSS Prevention
```javascript
/**
 * Sanitizar input del usuario
 */

function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Uso en componentes
function renderUserContent(content) {
  return `<div>${escapeHtml(content)}</div>`;
}
```

### 2. CSRF Protection
```javascript
/**
 * Token CSRF en requests
 */

API.interceptors.request.use(config => {
  const token = document.querySelector('meta[name="csrf-token"]')?.content;
  if (token) {
    config.headers['X-CSRF-Token'] = token;
  }
  return config;
});
```

### 3. Secure Storage
```javascript
/**
 * Encriptar datos sensibles en localStorage
 */

class SecureStorage {
  static encrypt(data, key) {
    // Simple XOR encryption (usar crypto-js en producción)
    return btoa(JSON.stringify(data));
  }
  
  static decrypt(encrypted, key) {
    return JSON.parse(atob(encrypted));
  }
  
  static setSecure(key, value) {
    const encrypted = this.encrypt(value);
    localStorage.setItem(key, encrypted);
  }
  
  static getSecure(key) {
    const encrypted = localStorage.getItem(key);
    if (!encrypted) return null;
    return this.decrypt(encrypted);
  }
}
```

---

## 📊 Analytics y Tracking

### Event Tracking
```javascript
/**
 * Tracking de eventos importantes
 */

class Analytics {
  static track(eventName, properties = {}) {
    // Enviar a backend o servicio de analytics
    const event = {
      name: eventName,
      properties: {
        ...properties,
        timestamp: Date.now(),
        userId: Store.getState('user.id'),
        sessionId: this.getSessionId()
      }
    };
    
    // Queue for batch send
    this.queue.push(event);
    
    if (this.queue.length >= 10) {
      this.flush();
    }
  }
  
  static flush() {
    if (this.queue.length === 0) return;
    
    API.analytics.batch(this.queue);
    this.queue = [];
  }
}

// Eventos importantes a trackear
Analytics.track('activity_started', { type: 'run' });
Analytics.track('activity_completed', { distance: 10, duration: 50 });
Analytics.track('territory_attacked', { territoryId, units: 10 });
Analytics.track('conquest_achieved', { territoryId });
Analytics.track('battle_joined', { battleId });
Analytics.track('team_created', { teamId });
Analytics.track('strava_connected');
```

---

## 🧪 Testing en Mobile

### 1. Responsive Testing
```javascript
/**
 * Helpers para testing responsive
 */

class ResponsiveTester {
  static viewports = {
    mobile: { width: 375, height: 667 }, // iPhone SE
    tablet: { width: 768, height: 1024 }, // iPad
    desktop: { width: 1920, height: 1080 }
  };
  
  static setViewport(device) {
    const { width, height } = this.viewports[device];
    window.resizeTo(width, height);
  }
  
  static isMobile() {
    return window.innerWidth < 768;
  }
  
  static isTablet() {
    return window.innerWidth >= 768 && window.innerWidth < 1024;
  }
}
```

### 2. Performance Testing
```javascript
/**
 * Medir performance
 */

class PerformanceMonitor {
  static measurePageLoad() {
    window.addEventListener('load', () => {
      const perfData = performance.timing;
      const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
      
      Analytics.track('page_load_time', {
        loadTime: pageLoadTime,
        page: window.location.pathname
      });
    });
  }
  
  static measureComponentRender(componentName, renderFn) {
    const start = performance.now();
    const result = renderFn();
    const end = performance.now();
    
    console.log(`${componentName} render: ${end - start}ms`);
    
    if (end - start > 16) { // > 1 frame (60fps)
      console.warn(`Slow render detected: ${componentName}`);
    }
    
    return result;
  }
}
```

---

## 📦 Build y Deploy

### Build Script
```javascript
// build.js

/**
 * Script de build para producción
 * 
 * 1. Minificar CSS
 * 2. Minificar JS
 * 3. Optimizar imágenes
 * 4. Generar service worker
 * 5. Crear manifest
 * 6. Calcular hashes de archivos
 */

const fs = require('fs');
const path = require('path');
const { minify } = require('terser');
const CleanCSS = require('clean-css');

async function build() {
  console.log('🏗️  Building...');
  
  // 1. Clean dist
  if (fs.existsSync('dist')) {
    fs.rmSync('dist', { recursive: true });
  }
  fs.mkdirSync('dist');
  
  // 2. Copy HTML
  copyFile('index.html', 'dist/index.html');
  
  // 3. Minify CSS
  const cssFiles = getFiles('css', '.css');
  for (const file of cssFiles) {
    await minifyCSS(file);
  }
  
  // 4. Minify JS
  const jsFiles = getFiles('js', '.js');
  for (const file of jsFiles) {
    await minifyJS(file);
  }
  
  // 5. Copy assets
  copyDir('assets', 'dist/assets');
  
  // 6. Generate service worker
  generateServiceWorker();
  
  // 7. Copy manifest
  copyFile('manifest.json', 'dist/manifest.json');
  
  console.log('✅ Build complete!');
}

build();
```

### Deploy to Render
```yaml
# render.yaml

services:
  # Static site para la PWA
  - type: web
    name: territory-conquest-pwa
    env: static
    buildCommand: npm run build
    staticPublishPath: ./dist
    headers:
      - path: /*
        name: Cache-Control
        value: public, max-age=3600
      - path: /service-worker.js
        name: Cache-Control
        value: no-cache
      - path: /assets/*
        name: Cache-Control
        value: public, max-age=31536000
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
```

---

## 🎯 Checklist de Implementación

### Fase 1: Core (2 semanas)
- [ ] Setup estructura de carpetas
- [ ] Implementar Router SPA
- [ ] Implementar Store global
- [ ] Implementar API Client
- [ ] Implementar Auth
- [ ] Implementar Storage (localStorage + IndexedDB)
- [ ] Implementar Event Bus
- [ ] Componentes base (Button, Input, Modal, Toast)
- [ ] CSS reset y variables
- [ ] Navegación (TopBar, BottomNav)

### Fase 2: Tracking (1 semana)
- [ ] LocationService (GPS tracking)
- [ ] TrackingPage (UI en vivo)
- [ ] ActivityService (gestión actividades)
- [ ] Cálculos (distancia, pace, calorías)
- [ ] Detección de hexágonos H3
- [ ] Guardar actividades offline
- [ ] Sincronización al volver online

### Fase 3: Mapa RISK (2 semanas)
- [ ] Integrar Leaflet.js
- [ ] MapService (renderizado)
- [ ] MapPage con zoom multi-nivel
- [ ] Renderizar territorios con hexágonos
- [ ] Renderizar batallas con animaciones
- [ ] Modal de detalle de territorio
- [ ] Interacciones del mapa (tap, zoom, pan)
- [ ] Filtros del mapa

### Fase 4: Conquista (1 semana)
- [ ] PostActivityPage (distribución de KM)
- [ ] AttackSlider component
- [ ] Sugerencias estratégicas
- [ ] Preview de ataque
- [ ] Ejecutar movimientos tácticos
- [ ] Animaciones de conquista
- [ ] Notificaciones de eventos

### Fase 5: Social (1 semana)
- [ ] TeamPage
- [ ] MembersList
- [ ] TeamStats
- [ ] Chat básico del equipo
- [ ] Invitar miembros
- [ ] Salir del equipo

### Fase 6: Rankings (3 días)
- [ ] RankingsPage
- [ ] Virtual scrolling
- [ ] Filtros de rankings
- [ ] Tabs (usuarios/equipos/zonas)
- [ ] Posición del usuario destacada

### Fase 7: Perfil (3 días)
- [ ] ProfilePage
- [ ] Editar perfil
- [ ] Stats del usuario
- [ ] Logros/Achievements
- [ ] Historial de actividades

### Fase 8: PWA (3 días)
- [ ] Service Worker
- [ ] Cache de assets
- [ ] Offline fallback
- [ ] Manifest.json
- [ ] Push notifications
- [ ] Background sync
- [ ] Iconos en todos los tamaños
- [ ] Splash screens

### Fase 9: Optimización (1 semana)
- [ ] Lazy loading de componentes
- [ ] Virtual scrolling
- [ ] Image lazy loading
- [ ] Request batching
- [ ] Memory management
- [ ] Animaciones optimizadas
- [ ] Performance monitoring

### Fase 10: Testing y Deploy (3 días)
- [ ] Testing responsivo
- [ ] Testing offline
- [ ] Testing en dispositivos reales
- [ ] Build script
- [ ] Deploy a Render
- [ ] Configurar dominio

---

## 📚 Recursos Necesarios

### Librerías Externas
```json
{
  "dependencies": {
    "leaflet": "^1.9.4",
    "h3-js": "^4.1.0"
  },
  "devDependencies": {
    "terser": "^5.19.0",
    "clean-css": "^5.3.2"
  }
}
```

### CDN Links (alternativa)
```html
<!-- Leaflet -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<!-- H3-js -->
<script src="https://unpkg.com/h3-js@4.1.0/dist/h3-js.umd.js"></script>
```

---

¡Arquitectura móvil completa lista! 📱⚔️🗺️

Total estimado: **8-10 semanas** de desarrollo para MVP completo. * Uso:
 * Toast.show({
 *   type: 'success',
 *   message: '¡Territorio conquistado!',
 *   duration: 3000,
 *   action: {
 *     text: 'Ver',
 *     callback: () => Router.navigate('/territory/123')
 *   }
 * });
 */
```

---

## 🔄 Flujos de Datos Detallados

### Flujo 1: Tracking de Actividad
```
Usuario tapa "Iniciar Entrenamiento"
↓
TrackingPage.mount()
↓
LocationService.startTracking()
├─ Pedir permisos GPS
├─ Iniciar GPS tracking (cada 5s)
├─ Iniciar contador de distancia
└─ Iniciar contador de tiempo
↓
Cada 5 segundos:
├─ GPS captura posición {lat, lng, timestamp}
├─ ActivityService.addPoint(point)
│   ├─ Calcular distancia desde último punto
│   ├─ Actualizar distancia total
│   ├─ Calcular pace
│   ├─ Detectar hexágonos atravesados (H3)
│   └─ Store.setState('tracking.currentActivity', data)
├─ TrackingPage actualiza UI (reactive)
└─ Cada 30s: Storage.saveActivityDraft() (offline backup)
↓
Usuario tapa "Pausar"
├─ LocationService.pauseTracking()
├─ Guardar estado
└─ Mostrar "Reanudar"
↓
Usuario tapa "Terminar"
├─ LocationService.stopTracking()
├─ Calcular stats finales
├─ Mostrar resumen
└─ Router.navigate('/activity/distribute', {activityId})
↓
PostActivityPage
├─ Mostrar defensa automática aplicada
├─ Cargar sugerencias estratégicas (API.risk.getSuggestions())
├─ Usuario distribuye KM
└─ Confirmar
    ↓
    ActivityService.finalizeActivity()
    ├─ API.activities.create()
    ├─ API.risk.executeMove() (por cada asignación)
    ├─ Events.emit('activity:completed')
    ├─ Toast.show('¡Actividad registrada!')
    └─ Router.navigate('/home')
        ↓
        HomePage actualiza con nuevos stats
```

### Flujo 2: Ataque a Territorio
```
Usuario en MapPage
↓
Tap en territorio enemigo
↓
Modal: TerritoryDetail
├─ Muestra stats del territorio
├─ Muestra control actual
├─ Botón "Atacar" visible
└─ Botón "Ver Historia"
↓
Usuario tapa "Atacar"
↓
Si NO tiene actividad reciente:
├─ Toast: "Necesitas correr primero"
└─ Botón "Ir a Tracking"
↓
Si SÍ tiene actividad reciente:
├─ Modal: AttackPlanner
│   ├─ Mostrar KM disponibles
│   ├─ Slider para seleccionar unidades
│   ├─ Preview de ataque (API.risk.previewAttack())
│   │   ├─ Probabilidad éxito
│   │   ├─ Hexágonos estimados a conquistar
│   │   └─ Recomendación (GO/RISKY/AVOID)
│   └─ Botón "Confirmar Ataque"
↓
Usuario ajusta slider y confirma
↓
RiskService.executeAttack()
├─ Validar disponibilidad de unidades
├─ API.risk.executeMove({
│     activityId,
│     moveType: 'attack',
│     toTerritoryId,
│     units,
│     km
│   })
├─ Response: {
│     success: true,
│     conquest_happened: boolean,
│     was_critical: boolean,
│     units_deployed: number
│   }
└─ Procesar resultado
    ↓
    Si conquest_happened = true:
    ├─ Animación de conquista
    ├─ Sound.play('conquest')
    ├─ Toast: "¡Territorio conquistado! 🏆"
    ├─ Events.emit('conquest:territoryGained')
    └─ Actualizar mapa (cambio de color)
    ↓
    Si conquest_happened = false:
    ├─ Toast: "Ataque registrado. +{units} unidades"
    └─ Actualizar stats del territorio
    ↓
    Store.setState('map.territories', updatedTerritories)
    MapPage re-renderiza automáticamente
```

### Flujo 3: Sincronización Offline
```
Usuario pierde conexión durante tracking
↓
LocationService detecta offline
├─ Events.emit('network:offline')
├─ Store.setState('offline.isOnline', false)
└─ Toast: "Modo offline. Datos guardados localmente."
↓
GPS sigue funcionando
├─ Puntos se guardan en Storage.db.activities
└─ UI muestra indicador "Offline ⚡"
↓
Usuario termina actividad
├─ ActivityService guarda completo en IndexedDB
├─ SyncService.addToPendingQueue(activity)
└─ Toast: "Actividad guardada. Se sincronizará al conectar."
↓
Usuario recupera conexión
↓
Events.emit('network:online')
├─ Store.setState('offline.isOnline', true)
├─ SyncService.syncPending()
│   ├─ Obtener cola de pendientes
│   ├─ Para cada item:
│   │   ├─ API.activities.create(item)
│   │   ├─ Si success: Storage.db.syncQueue.delete(item)
│   │   └─ Si error: Mantener en cola, retry later
│   └─ Events.emit('sync:completed', {synced: count})
└─ Toast: "✓ {count} actividades sincronizadas"
↓
HomePage refresca datos del servidor
```

### Flujo 4: Push Notification
```
Territorio del usuario es atacado
↓
Backend detecta evento
├─ Calcula impacto
└─ Si crítico: Envía push notification
↓
Service Worker recibe mensaje
├─ service-worker.js
├─ self.addEventListener('push', event)
└─ Muestra notificación
    {
      title: "⚠️ ¡TERRITORIO BAJO ATAQUE!",
      body: "Francia atacó Cataluña. -5% control.",
      icon: "/assets/icons/icon-192x192.png",
      badge: "/assets/icons/badge-72x72.png",
      vibrate: [200, 100, 200],
      data: {
        url: "/battles/123",
        battleId: "123"
      },
      actions: [
        {action: 'defend', title: 'Defender'},
        {action: 'view', title: 'Ver'}
      ]
    }
↓
Usuario tapa notificación
↓
Service Worker: notificationclick event
├─ Si action = 'defend':
│   └─ clients.openWindow('/tracking')
├─ Si action = 'view':
│   └─ clients.openWindow('/battles/123')
└─ Default: clients.openWindow(notification.data.url)
↓
App abre en página específica
├─ Router detecta deep link
└─ Carga BattleDetailPage con battleId
```

---

## 🎯 Service Workers Detallado

### service-worker.js
```javascript
/**
 * Service Worker para PWA
 * 
 * Funcionalidades:
 * 1. Cache de assets estáticos (precache)
 * 2. Cache de API responses (runtime cache)
 * 3. Offline fallback
 * 4. Background sync
 * 5. Push notifications
 * 
 * Estrategias de cache:
 * 
 * Assets estáticos (CSS, JS, images):
 * → Cache First (con fallback a network)
 * 
 * API calls:
 * → Network First (con fallback a cache)
 * 
 * Mapas/tiles:
 * → Cache First (optimización)
 * 
 * User data:
 * → Network Only (siempre fresco)
 */

const CACHE_VERSION = 'v1.0.0';
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const API_CACHE = `api-${CACHE_VERSION}`;
const MAP_CACHE = `map-${CACHE_VERSION}`;

// Assets para precache
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/css/reset.css',
  '/css/variables.css',
  '/css/animations.css',
  '/css/components.css',
  '/css/layouts.css',
  '/js/app.js',
  '/js/core/router.js',
  '/js/core/store.js',
  '/manifest.json',
  '/assets/icons/icon-192x192.png',
  '/assets/icons/icon-512x512.png'
];

// Install event
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Activate event
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => {
        return Promise.all(
          keys
            .filter(key => key !== STATIC_CACHE && key !== API_CACHE)
            .map(key => caches.delete(key))
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstStrategy(request));
  }
  // Map tiles
  else if (url.pathname.includes('/tiles/')) {
    event.respondWith(cacheFirstStrategy(request, MAP_CACHE));
  }
  // Static assets
  else {
    event.respondWith(cacheFirstStrategy(request, STATIC_CACHE));
  }
});

// Push notification
self.addEventListener('push', event => {
  const data = event.data.json();
  
  const options = {
    body: data.body,
    icon: '/assets/icons/icon-192x192.png',
    badge: '/assets/icons/badge-72x72.png',
    vibrate: [200, 100, 200],
    data: data.data,
    actions: data.actions || []
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  const urlToOpen = event.notification.data.url || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window' })
      .then(clientList => {
        // Si ya hay ventana abierta, focus
        for (let client of clientList) {
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }
        // Si no, abrir nueva
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Background sync
self.addEventListener('sync', event => {
  if (event.tag === 'sync-activities') {
    event.waitUntil(syncPendingActivities());
  }
});
```

---

## 📦 Gestión de Estado (Store)

### Store Implementation
```javascript
/**
 * Store global simple estilo Redux
 */

class Store {
  constructor(initialState = {}) {
    this.state = initialState;
    this.listeners = new Map(); // path -> Set<callbacks>
  }

  // Get state
  getState(path = null) {
    if (!path) return this.state;
    
    return path.split('.').reduce((obj, key) => {
      return obj?.[key];
    }, this.state);
  }

  // Set state
  setState(path, value) {
    const keys = path.split('.');
    const lastKey = keys.pop();
    
    // Navigate to parent
    const parent = keys.reduce((obj, key) => {
      if (!obj[key]) obj[key] = {};
      return obj[key];
    }, this.state);
    
    // Set value
    const oldValue = parent[lastKey];
    parent[lastKey] = value;
    
    // Notify listeners
    this.notify(path, value, oldValue);
    
    // Persist critical data
    this.persistCriticalData();
  }

  // Subscribe to changes
  subscribe(path, callback) {
    if (!this.listeners.has(path)) {
      this.listeners.set(path, new Set());
    }
    
    this.listeners.get(path).add(callback);
    
    // Return unsubscribe function
    return () => {
      const callbacks = this.listeners.get(path);
      if (callbacks) {
        callbacks.delete(callback);
      }
    };
  }

  // Notify listeners
  notify(path, newValue, oldValue) {
    // Notify exact path listeners
    const callbacks = this.listeners.get(path);
    if (callbacks) {
      callbacks.forEach(cb => cb(newValue, oldValue));
    }
    
    // Notify parent path listeners
    const pathParts = path.split('.');
    for (let i = pathParts.length - 1; i >= 0; i--) {
      const parentPath = pathParts.slice(0, i).join('.');
      const parentCallbacks = this.listeners.get(parentPath);
      if (parentCallbacks) {
        const parentValue = this.getState(parentPath);
        parentCallbacks.forEach(cb => cb(parentValue));
      }
    }
  }

  // Dispatch actions
  dispatch(action, payload) {
    switch (action) {
      case 'AUTH_LOGIN':
        this.setState('auth.isAuthenticated', true);
        this.setState('auth.token', payload.token);
        this.setState('user', payload.user);
        break;
        
      case 'AUTH_LOGOUT':
        this.setState('auth.isAuthenticated', false);
        this.setState('auth.token', null);
        this.setState('user', null);
        Storage.clear(); // Clear all local data
        break;
        
      case 'TRACKING_START':
        this.setState('tracking.isActive', true);
        this.setState('tracking.currentActivity', payload);
        break;
        
      case 'TRACKING_UPDATE':
        const current = this.getState('tracking.currentActivity');
        this.setState('tracking.currentActivity', {
          ...current,
          ...payload
        });
        break;
        
      case 'TRACKING_STOP':
        this.setState('tracking.isActive', false);
        break;
        
      case 'MAP_UPDATE_TERRITORIES':
        this.setState('map.territories', payload);
        break;
        
      case 'BATTLE_UPDATE':
        const battles = this.getState('battles.active');
        const updated = battles.map(b => 
          b.id === payload.id ? payload : b
        );
        this.setState('battles.active', updated);
        break;
        
      case 'NOTIFICATION_ADD':
        const notifications = this.getState('notifications.items') || [];
        this.setState('notifications.items', [payload, ...notifications]);
        this.setState('notifications.unread', 
          this.getState('notifications.unread') + 1
        );
        break;
        
      case 'NETWORK_STATUS':
        this.setState('offline.isOnline', payload);
        break;
        
      default:
        console.warn('Unknown action:', action);
    }
  }

  // Persist critical data to localStorage
  persistCriticalData() {
    const criticalPaths = [
      'auth.token',
      'auth.isAuthenticated',
      'user.id',
      'user.username',
      'tracking.currentActivity'
    ];
    
    const dataToSave = {};
    criticalPaths.forEach(path => {
      dataToSave[path] = this.getState(path);
    });
    
    Storage.set('store_critical', dataToSave);
  }

  // Restore from storage
  restore() {
    const saved = Storage.get('store_critical');
    if (saved) {
      Object.keys(saved).forEach(path => {
        this.setState(path, saved[path]);
      });
    }
  }

  // Reset store
  reset() {
    this.state = getInitialState();
    this.listeners.clear();
  }
}

// Initial state
function getInitialState() {
  return {
    user: null,
    auth: {
      isAuthenticated: false,
      token: null,
      tokenExpiry: null
    },
    map: {
      currentZoom: 'world',
      territories: [],
      selectedTerritory: null,
      filters: {
        showOnlyMine: false,
        showBattles: true,
        showTeam: false
      }
    },
    tracking: {
      isActive: false,
      isPaused: false,
      currentActivity: null
    },
    battles: {
      active: [],
      userRelated: [],
      critical: []
    },
    notifications: {
      unread: 0,
      items: []
    },
    offline: {
      isOnline: navigator.onLine,
      pendingSync: [],
      lastSync: null
    },
    ui: {
      loading: false,
      modal: null,
      toast: null,
      bottomNav: 'visible'
    }
  };
}

// Export singleton
export default new Store(getInitialState());
```

---

## 🗺️ Sistema de Mapas (MapService)

### MapService Implementation
```javascript
/**
 * Gestión del mapa con Leaflet
 */

import L from 'leaflet';
import { h3ToGeo, h3ToGeoBoundary } from 'h3-js';

class MapService {
  constructor() {
    this.map = null;
    this.layers = {
      territories: null,
      hexagons: null,
      battles: null,
      userPosition: null
    };
    this.currentZoom = 'world';
  }

  // Initialize map
  init(containerId, options = {}) {
    const defaultOptions = {
      center: [41.3851, 2.1734], // Barcelona
      zoom: 6,
      minZoom: 3,
      maxZoom: 18,
      zoomControl: false // Custom controls
    };

    this.map = L.map(containerId, { ...defaultOptions, ...options });

    // Add tile layer (OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19
    }).addTo(this.map);

    // Initialize layers
    this.layers.territories = L.layerGroup().addTo(this.map);
    this.layers.hexagons = L.layerGroup().addTo(this.map);
    this.layers.battles = L.layerGroup().addTo(this.map);
    this.layers.userPosition = L.layerGroup().addTo(this.map);

    // Map events
    this.map.on('zoomend', () => this.handleZoomChange());
    this.map.on('moveend', () => this.handleMoveEnd());

    return this.map;
  }

  // Render territories
  renderTerritories(territories) {
    this.layers.territories.clearLayers();

    territories.forEach(territory => {
      // Get H3 hexagons
      const hexagons = territory.h3_indexes || [];
      
      hexagons.forEach(h3Index => {
        const boundary = h3ToGeoBoundary(h3Index);
        const latlngs = boundary.map(([lat, lng]) => [lat, lng]);

        // Create polygon
        const polygon = L.polygon(latlngs, {
          color: this.getBorderColor(territory),
          fillColor: territory.controller?.color || '#9E9E9E',
          fillOpacity: territory.is_under_attack ? 0.7 : 0.5,
          weight: territory.is_under_attack ? 3 : 1,
          className: territory.is_under_attack ? 'battle-animation' : ''
        });

        // Add tooltip
        polygon.bindTooltip(`
          <strong>${territory.name}</strong><br>
          ${territory.controller?.name || 'Neutral'}<br>
          ${territory.units} unidades
        `, {
          permanent: false,
          direction: 'top'
        });

        // Add popup
        polygon.bindPopup(this.createTerritoryPopup(territory));

        // Click event
        polygon.on('click', () => {
          Events.emit('map:territoryClick', territory);
        });

        polygon.addTo(this.layers.territories);
      });
    });
  }

  // Render individual hexagons (zoomed in)
  renderHexagons(hexagons) {
    this.layers.hexagons.clearLayers();

    hexagons.forEach(hex => {
      const boundary = h3ToGeoBoundary(hex.h3_index);
      const latlngs = boundary.map(([lat, lng]) => [lat, lng]);

      const polygon = L.polygon(latlngs, {
        color: hex.is_contested ? '#FF5722' : '#424242',
        fillColor: hex.controller_color || '#9E9E9E',
        fillOpacity: 0.6,
        weight: hex.is_contested ? 2 : 1
      });

      polygon.bindTooltip(`
        Hexágono ${hex.h3_index.substring(0, 8)}...<br>
        Control: ${hex.control_strength} km<br>
        ${hex.is_contested ? '⚔️ En disputa' : ''}
      `);

      polygon.addTo(this.layers.hexagons);
    });
  }

  // Render battle markers
  renderBattles(battles) {
    this.layers.battles.clearLayers();

    battles.forEach(battle => {
      const icon = L.divIcon({
        className: 'battle-marker',
        html: `
          <div class="battle-marker-content">
            ⚔️
            <div class="battle-pulse"></div>
          </div>
        `,
        iconSize: [40, 40]
      });

      const marker = L.marker(
        [battle.territory_lat, battle.territory_lng],
        { icon }
      );

      marker.bindPopup(this.createBattlePopup(battle));
      marker.on('click', () => {
        Events.emit('map:battleClick', battle);
      });

      marker.addTo(this.layers.battles);
    });
  }

  // Show user position
  showUserPosition(lat, lng, accuracy = 50) {
    this.layers.userPosition.clearLayers();

    // Accuracy circle
    L.circle([lat, lng], {
      radius: accuracy,
      color: '#2196F3',
      fillColor: '#2196F3',
      fillOpacity: 0.1,
      weight: 1
    }).addTo(this.layers.userPosition);

    // User marker
    const icon = L.divIcon({
      className: 'user-marker',
      html: '<div class="user-marker-dot"></div>',
      iconSize: [20, 20]
    });

    L.marker([lat, lng], { icon })
      .addTo(this.layers.userPosition);
  }

  // Helper: Get border color based on status
  getBorderColor(territory) {
    if (territory.is_under_attack) return '#FF5722';
    if (territory.is_capital) return '#FFD700';
    return '#424242';
  }

  // Helper: Create territory popup
  createTerritoryPopup(territory) {
    return `
      <div class="territory-popup">
        <h3>${territory.name} ${territory.icon || ''}</h3>
        <div class="controller">
          <span>${territory.controller?.flag || ''}</span>
          <span>${territory.controller?.name || 'Neutral'}</span>
        </div>
        <div class="stats">
          <div>💪 ${territory.units} unidades</div>
          <div>📅 ${territory.days_controlled} días</div>
          ${territory.defense_bonus ? `<div>🛡️ +${territory.defense_bonus * 100}% defensa</div>` : ''}
        </div>
        ${territory.is_under_attack ? `
          <div class="battle-status">
            ⚔️ Bajo ataque<br>
            Progreso enemigo: ${territory.battle_progress}%
          </div>
        ` : ''}
        <button class="btn-primary" onclick="handleTerritoryAction('${territory.id}')">
          ${territory.is_mine ? 'Defender' : 'Atacar'}
        </button>
      </div>
    `;
  }

  // Helper: Create battle popup
  createBattlePopup(battle) {
    return `
      <div class="battle-popup">
        <h3>⚔️ Batalla Activa</h3>
        <div class="battle-sides">
          <div>
            ${battle.defender_flag} ${battle.defender_name}<br>
            ${battle.defender_units} unidades
          </div>
          <div class="vs">VS</div>
          <div>
            ${battle.attacker_flag} ${battle.attacker_name}<br>
            ${battle.attacker_units} unidades
          </div>
        </div>
        <div class="battle-progress">
          <div class="progress-bar">
            <div class="progress-fill" style="width: ${battle.conquest_progress}%"></div>
          </div>
          <span>${battle.conquest_progress}% hacia conquista</span>
        </div>
        <button class="btn-danger" onclick="handleBattleAction('${battle.id}')">
          Ver Detalle
        </button>
      </div>
    `;
  }

  // Zoom to territory
  zoomToTerritory(territory) {
    if (territory.h3_indexes && territory.h3_indexes.length > 0) {
      const bounds = [];
      territory.h3_indexes.forEach(h3 => {
        const [lat, lng] = h3ToGeo(h3);
        bounds.push([lat, lng]);
      });
      this.map.fitBounds(bounds, { padding: [50, 50] });
    }
  }

  // Handle zoom change
  handleZoomChange() {
    const zoom = this.map.getZoom();
    
    // Determine what to show based on zoom
    if (zoom < 6) {
      this.currentZoom = 'world';
      this.layers.hexagons.clearLayers();
    } else if (zoom < 10) {
      this.currentZoom = 'country';
    } else if (zoom < 14) {
      this.currentZoom = 'city';
    } else {
      this.currentZoom = 'hexagon';
      // Load and render individual hexagons
    }

    Events.emit('map:zoomChange', this.currentZoom);
  }

  // Cleanup
  destroy() {
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
  }
}

export default new MapService();
```

---

## 📲 Instalación PWA

### manifest.json
```json
{
  "name": "Territory Conquest",
  "short_name": "TerritoryConquest",
  "description": "Conquista territorial mediante deporte",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#FFFFFF",
  "theme_color": "#004D98",
  "orientation": "portrait",
  "scope": "/",
  "icons": [
    {
      "src": "/assets/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/assets/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/assets/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/assets/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/assets/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/assets/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/assets/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/assets/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ],
  "shortcuts": [
    {
      "name": "Iniciar Entreno",
      "short_name": "Track",
      "description": "Empezar tracking",
      "url": "/tracking",
      "icons": [{ "src": "/assets/icons/shortcut-track.png", "sizes": "96x96" }]
    },
    {
      "name": "Ver Mapa",
      "short_name": "Mapa",
      "description": "Abrir mapa RISK",
      "url": "/map",
      "icons": [{ "src": "/assets/icons/shortcut-map.png", "sizes": "96x96" }]
    },
    {
      "name": "Batallas",
      "short_name": "Batallas",
      "description": "Ver batallas activas",
      "url": "/battles",
      "icons": [{ "src": "/assets/icons/shortcut-battle.png", "sizes": "96x96" }]
    }
  ],
  "categories": ["sports", "games", "health"],
  "prefer_related_applications": false
}
```

---

## ⚡ Optim│  │ ████████░░ 8 unidades               │ │
│  │ Éxito: 65% | Crítico: ⭐⭐⭐      │ │
│  │                                   │ │
│  │ [⚔️ ATACAR CON 8]  [VER MAPA]    │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ 🟡 MEDIO                          │ │
│  │ MADRID (Rivalidad)                │ │
│  │ Empatados en ranking              │ │
│  │                                   │ │
│  │ ███░░░░░░░ 3 unidades             │ │
│  │ Éxito: 35% | Simbólico: ⭐       │ │
│  │                                   │ │
│  │ [⚔️ ATACAR CON 3]  [VER MAPA]    │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ PERSONALIZADO                     │ │
│  │ Seleccionar en mapa               │ │
│  │ [🗺️ ABRIR MAPA TÁCTICO]          │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Restante: 10 unidades                 │
│  [🛡️ SOLO DEFENDER] [✅ CONFIRMAR]    │
└─────────────────────────────────────────┘

Componentes:
- AutoDefenseIndicator (ya aplicado)
- StrategicSuggestions (lista priorizada)
- AttackSlider (asignar unidades)
- RemainingUnits (contador)
- MapButton (abrir mapa táctico)
- ActionButtons

Interacciones:
- Slider para ajustar unidades
- Tap sugerencia → Pre-selecciona unidades
- Tap "Ver Mapa" → Abre MapPage con modo selección
- Tap "Confirmar" → Ejecuta ataques
- "Solo Defender" → Skip distribución

State local:
- totalUnits: 10
- allocations: [
    {targetId, targetName, units, priority}
  ]
- suggestions: []
- remainingUnits: 10

Validaciones:
- No puede exceder total de unidades
- Mínimo 1 unidad por ataque
- Confirmar antes de enviar
```

### 5. BattlesPage (Batallas Activas)
```
┌─────────────────────────────────────────┐
│  [←]  Batallas Activas        [🔄]     │
├─────────────────────────────────────────┤
│  📊 GLOBAL: 23 batallas activas        │
│  Tu participación: 3 batallas          │
│                                         │
│  [Todas] [Mis Batallas] [Críticas]     │  ← Tabs
├─────────────────────────────────────────┤
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ ⚔️ CATALUÑA                       │ │
│  │                                   │ │
│  │ 🇪🇸 España    VS    Francia 🇫🇷  │ │
│  │    156                142         │ │
│  │ ████████      ███████             │ │
│  │   52%           48%               │ │
│  │                                   │ │
│  │ Hexágonos en disputa: 24         │ │
│  │ ⬢⬢⬢⬢🇪🇸 | ⚔️⚔️⚔️ | ⬢⬢⬢🇫🇷      │ │
│  │                                   │ │
│  │ 🔴 Francia ganando últimas 24h   │ │
│  │ Tu aporte: 12 unidades           │ │
│  │                                   │ │
│  │ [⚔️ REFORZAR] [👁️ VER DETALLE]   │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ ⚔️ FRONTERA PIRINEOS             │ │
│  │                                   │ │
│  │ 🇪🇸 España    VS    Francia 🇫🇷  │ │
│  │    89                 118         │ │
│  │ ██████        █████████           │ │
│  │   43%           57%               │ │
│  │                                   │ │
│  │ 🔴🔴 CRÍTICO - Conquista en 12h  │ │
│  │ Se necesitan: 30 unidades        │ │
│  │                                   │ │
│  │ [🚨 DEFENDER YA] [👁️ DETALLE]    │ │
│  └───────────────────────────────────┘ │
│                                         │
│  [Cargar más...]                       │
└─────────────────────────────────────────┘

Componentes:
- BattleFilters (tabs)
- BattleCard (completo con stats)
- ProgressBar (visual % control)
- ThreatIndicator (nivel crítico)
- ActionButtons

Interacciones:
- Pull to refresh
- Tap card → Detalle batalla
- Tap "Reforzar" → Ir a activities
- Swipe card → Opciones (notificar, compartir)
- Filter por relevancia

State local:
- activeTab: 'all'|'mine'|'critical'
- battles: []
- userParticipation: {}

Auto-refresh:
- Cada 30 segundos
- Push notifications para cambios críticos
```

### 6. BattleDetailPage (Detalle Batalla)
```
┌─────────────────────────────────────────┐
│  [←]  Batalla: Cataluña       [⋮]      │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │    MAPA DE HEXÁGONOS            │   │
│  │                                 │   │
│  │  ⬢⬢⬢⬢🇪🇸  |  ⚔️⚔️⚔️  |  ⬢⬢⬢🇫🇷 │   │
│  │  ⬢⬢⬢⬢⬢⬢  |  ⚔️⚔️⚔️  |  ⬢⬢⬢⬢⬢ │   │
│  │  ⬢⬢⬢⬢⬢⬢  |  ⚔️⚔️    |  ⬢⬢⬢⬢⬢ │   │
│  │                                 │   │
│  │  España: 10 hex | Francia: 14  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ESTADO ACTUAL                          │
│  🇪🇸 España: 156 unidades (52%)        │
│  ████████████░░░░░░░░                  │
│  🇫🇷 Francia: 142 unidades (48%)       │
│  ████████████░░░░░░░░                  │
│                                         │
│  📊 PROGRESO DE CONQUISTA               │
│  Francia: 58% hacia conquista          │
│  ███████████████████████░░░░░ 70%      │
│  🔴 ¡Falta solo 12% para perder!       │
│                                         │
│  ⏱️ DURACIÓN: 12 días                  │
│  📈 TENDENCIA: Francia +8% última 24h  │
│                                         │
├─────────────────────────────────────────┤
│  ÚLTIMOS MOVIMIENTOS                    │
│                                         │
│  🏃 @coureur_fr +15 unidades           │
│  🕐 Hace 5 minutos                     │
│                                         │
│  🏃 @runner_bcn +10 unidades (TÚ)     │
│  🕐 Hace 12 minutos                    │
│                                         │
│  🏃 @jogger_esp +8 unidades            │
│  🕐 Hace 23 minutos                    │
│                                         │
│  [Ver todos los 234 movimientos]       │
│                                         │
├─────────────────────────────────────────┤
│  TOP PARTICIPANTES                      │
│  1. @coureur_fr 🇫🇷 - 89 unidades     │
│  2. @runner_bcn 🇪🇸 - 67 unidades     │
│  3. @sprinter_cat 🇪🇸 - 45 unidades   │
│                                         │
├─────────────────────────────────────────┤
│  [⚔️ REFORZAR]  [📢 NOTIFICAR EQUIPO]  │
│  [📊 STATS]     [🔔 ALERTAS]           │
└─────────────────────────────────────────┘

Componentes:
- HexagonMap (batalla en detalle)
- ProgressIndicators
- Timeline (movimientos recientes)
- ParticipantsList
- ActionButtons

Interacciones:
- Tap hexágono → Info del hexágono
- Tap participante → Ver perfil
- Tap "Reforzar" → Ir a crear actividad
- Tap "Notificar equipo" → Compartir alerta
- Live updates cada 10 segundos

State local:
- battleDetail: {}
- recentMoves: []
- topParticipants: []
- hexagonStates: []
```

### 7. TeamPage (Vista Equipo)
```
┌─────────────────────────────────────────┐
│  [←]  Barcelona Runners       [⚙️]     │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │  [LOGO]  Barcelona Runners      │   │
│  │          #004D98                │   │
│  │                                 │   │
│  │  12 miembros | 345 km | Rank #3│   │
│  │  Zonas controladas: 23          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [📊 Stats] [👥 Miembros] [🗺️ Zonas]  │  ← Tabs
├─────────────────────────────────────────┤
│  STATS DEL EQUIPO                      │
│                                         │
│  Esta semana:                           │
│  ├─ 127 km acumulados                  │
│  ├─ 8 zonas conquistadas                │
│  ├─ 3 batallas ganadas                  │
│  └─ 2 territorios defendidos            │
│                                         │
│  📈 Gráfica semanal                     │
│  ┌─────────────────────────────────┐   │
│  │ KM │ ▆                          │   │
│  │ 50 │ █                          │   │
│  │ 25 │ █ ▆ █ ▆ █ █ █              │   │
│  │  0 │ L M X J V S D              │   │
│  └─────────────────────────────────┘   │
│                                         │
│  TOP CONTRIBUTORS                       │
│  1. 🥇 @runner_bcn - 87 km             │
│  2. 🥈 @jogger_cat - 65 km             │
│  3. 🥉 @sprinter - 48 km               │
│                                         │
│  OBJETIVOS DEL EQUIPO                   │
│  ┌───────────────────────────────────┐ │
│  │ 🎯 Conquistar Badalona            │ │
│  │ ████████░░ 78% completado         │ │
│  │ Faltan: 5 hexágonos               │ │
│  └───────────────────────────────────┘ │
│                                         │
│  [💬 CHAT] [📢 COORDINAR ATAQUE]       │
└─────────────────────────────────────────┘

Tab MIEMBROS:
│  MIEMBROS (12)              [+ Invitar] │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ 👤 @runner_bcn                    │ │
│  │    87 km | 870 pts | ⭐ Capitán  │ │
│  │    [Ver perfil] [Mensaje]        │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ 👤 @jogger_cat                    │ │
│  │    65 km | 650 pts                │ │
│  │    [Ver perfil] [Mensaje]        │ │
│  └───────────────────────────────────┘ │

Tab ZONAS:
│  ZONAS CONTROLADAS (23)     [Ver Mapa] │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ 📍 Gràcia                         │ │
│  │    Control: 78% | 12 hexágonos   │ │
│  │    🔴 Bajo ataque                │ │
│  │    [DEFENDER]                    │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ 📍 Eixample                       │ │
│  │    Control: 92% | 18 hexágonos   │ │
│  │    ✅ Seguro                     │ │
│  └───────────────────────────────────┘ │

Componentes:
- TeamHeader
- TeamTabs
- TeamStats (gráficas)
- MembersList
- ZonesList
- TeamChat (simple)
- TeamGoals

State local:
- teamData: {}
- activeTab: 'stats'|'members'|'zones'
- members: []
- zones: []
- stats: {}
```

### 8. RankingsPage (Rankings y Leaderboards)
```
┌─────────────────────────────────────────┐
│  [←]  Rankings                [🔄]     │
├─────────────────────────────────────────┤
│  [👥 Usuarios] [🏆 Equipos] [🗺️ Zonas] │  ← Tabs
│  [📊 Puntos ▼] [📏 KM] [⚔️ Zonas]      │  ← Metrics
├─────────────────────────────────────────┤
│                                         │
│  🎯 TU POSICIÓN                        │
│  ┌───────────────────────────────────┐ │
│  │ #1,234 de 15,000 en España       │ │
│  │ Top 10% 🎉                        │ │
│  │                                   │ │
│  │ 156 km | 1,567 pts               │ │
│  │ ↑ 50 posiciones esta semana      │ │
│  └───────────────────────────────────┘ │
│                                         │
│  TOP 100                                │
│                                         │
│  1. 🥇 @legend_runner                  │
│     2,845 pts | 284 km | 45 zonas      │
│     🇪🇸 España                         │
│                                         │
│  2. 🥈 @speed_demon                    │
│     2,734 pts | 267 km | 42 zonas      │
│     🇪🇸 España                         │
│                                         │
│  3. 🥉 @marathon_master                │
│     2,598 pts | 259 km | 38 zonas      │
│     🇫🇷 Francia                        │
│                                         │
│  ...                                    │
│                                         │
│  234. 👤 @runner_bcn (TÚ)              │
│       1,567 pts | 156 km | 12 zonas    │
│       🇪🇸 España                       │
│                                         │
│  ...                                    │
│                                         │
│  [Cargar más...]                       │
│                                         │
├─────────────────────────────────────────┤
│  FILTROS                                │
│  [ ] Solo mi país                       │
│  [ ] Solo mi ciudad                     │
│  [ ] Solo mi equipo                     │
└─────────────────────────────────────────┘

Tab EQUIPOS:
│  TOP EQUIPOS                            │
│                                         │
│  1. 🥇 Madrid Warriors                  │
│     12,567 pts | 1,256 km              │
│     Miembros: 45 | Zonas: 89           │
│                                         │
│  2. 🥈 Barcelona Runners                │
│     9,876 pts | 987 km                 │
│     Miembros: 38 | Zonas: 67           │

Tab ZONAS:
│  ZONAS MÁS ACTIVAS                      │
│                                         │
│  1. 📍 Barcelona                        │
│     45,678 km total                    │
│     Controlado por: Barcelona Runners  │
│     Batallas: 23 activas               │

Componentes:
- RankingTabs
- MetricSelector
- UserPosition (destacado)
- RankingList (virtualized)
- FilterPanel

Interacciones:
- Tap usuario → Ver perfil
- Tap equipo → Ver equipo
- Infinite scroll
- Pull to refresh
- Filter options

State local:
- activeTab: 'users'
- metric: 'points'
- rankings: []
- userPosition: {}
- filters: {}
```

### 9. ProfilePage (Perfil Usuario)
```
┌─────────────────────────────────────────┐
│  [←]  Perfil                  [✏️]     │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │     [AVATAR]                    │   │
│  │    @runner_bcn                  │   │
│  │    Juan García                  │   │
│  │    🇪🇸 Barcelona                │   │
│  │                                 │   │
│  │  Miembro desde: Oct 2025       │   │
│  └─────────────────────────────────┘   │
│                                         │
│  📊 ESTADÍSTICAS                       │
│  ┌───────────────────────────────────┐ │
│  │  156 km      1,567 pts     12    │ │
│  │  Total       Puntos     Zonas    │ │
│  └───────────────────────────────────┘ │
│                                         │
│  🏆 RANKINGS                           │
│  ├─ Mundial: #12,456 de 500,000       │
│  ├─ España: #1,234 de 15,000          │
│  ├─ Cataluña: #456 de 5,000           │
│  └─ Barcelona: #234 de 3,000          │
│                                         │
│  ⚔️ CONQUISTA                          │
│  ├─ Territorios controlados: 12        │
│  ├─ Batallas participadas: 23          │
│  ├─ Conquistas logradas: 5             │
│  └─ Territorios defendidos: 8          │
│                                         │
│  🏃 ACTIVIDADES                        │
│  ├─ Total actividades: 47              │
│  ├─ Promedio semanal: 3                │
│  ├─ Racha actual: 5 días 🔥           │
│  └─ Mejor racha: 12 días               │
│                                         │
│  🏅 LOGROS (8/25)                      │
│  ┌─────┬─────┬─────┬─────┬─────┐     │
│  │ 🏅  │ ⭐  │ 🏆  │ 🎯  │ 🔒  │     │
│  │5K   │10K  │42K  │Conq │???  │     │
│  └─────┴─────┴─────┴─────┴─────┘     │
│  [Ver todos]                           │
│                                         │
│  👥 EQUIPO                             │
│  Barcelona Runners                      │
│  12 miembros | Rank #3                 │
│  [Ver equipo]                           │
│                                         │
│  📅 ACTIVIDADES RECIENTES               │
│  10/15 - 10 km - Run                   │
│  10/14 - 5 km - Run                    │
│  10/12 - 8 km - Run                    │
│  [Ver todas]                            │
│                                         │
│  [⚙️ CONFIGURACIÓN]  [🚪 CERRAR SESIÓN]│
└─────────────────────────────────────────┘

Componentes:
- ProfileHeader (avatar, nombre)
- StatsGrid (métricas principales)
- RankingsDisplay
- ConquestStats
- ActivityStats
- AchievementsGrid
- TeamCard
- RecentActivitiesList

Interacciones:
- Tap "Editar" → Editar perfil
- Tap logro → Ver detalle
- Tap equipo → Ir a TeamPage
- Tap actividad → Ver detalle
- Tap stats → Ver desglose

State local:
- profileData: {}
- stats: {}
- achievements: []
- recentActivities: []
```

---

## 🎨 Sistema de Diseño (Design System)

### Colores (CSS Variables)
```css
:root {
  /* Primary */
  --color-primary: #004D98;      /* Azul Barcelona */
  --color-primary-light: #2D7DC6;
  --color-primary-dark: #003366;
  
  /* Secondary */
  --color-secondary: #FCDD09;    /* Amarillo Cataluña */
  --color-secondary-light: #FFE84D;
  --color-secondary-dark: #C4A900;
  
  /* Neutrals */
  --color-black: #1A1A1A;
  --color-gray-900: #2D2D2D;
  --color-gray-800: #424242;
  --color-gray-600: #757575;
  --color-gray-400: #BDBDBD;
  --color-gray-200: #E0E0E0;
  --color-gray-100: #F5F5F5;
  --color-white: #FFFFFF;
  
  /* Semantic */
  --color-success: #4CAF50;
  --color-warning: #FF9800;
  --color-error: #F44336;
  --color-info: #2196F3;
  
  /* Territory Colors */
  --color-spain: #AA151B;
  --color-france: #0055A4;
  --color-neutral: #9E9E9E;
  --color-battle: #FF5722;
  --color-conquered: #FFD700;
  
  /* Backgrounds */
  --bg-primary: #FFFFFF;
  --bg-secondary: #F5F5F5;
  --bg-tertiary: #E8E8E8;
  --bg-dark: #1A1A1A;
  --bg-overlay: rgba(0, 0, 0, 0.5);
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
  --shadow-xl: 0 20px 25px rgba(0,0,0,0.15);
  
  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;
  
  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;
  
  /* Typography */
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-base: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;
  --font-size-3xl: 30px;
  --font-size-4xl: 36px;
  
  /* Z-index */
  --z-modal: 1000;
  --z-toast: 2000;
  --z-loading: 3000;
}
```

### Componentes Base

#### Button
```javascript
/**
 * Botón reutilizable
 * 
 * Variantes:
 * - primary (azul sólido)
 * - secondary (amarillo sólido)
 * - outline (borde, fondo transparente)
 * - ghost (sin borde ni fondo)
 * - danger (rojo sólido)
 * - success (verde sólido)
 * 
 * Tamaños:
 * - sm (pequeño)
 * - md (mediano - default)
 * - lg (grande)
 * - xl (extra grande)
 * - block (ancho completo)
 * 
 * Estados:
 * - normal
 * - hover
 * - active (pressed)
 * - disabled
 * - loading (con spinner)
 * 
 * Props:
 * - variant: string
 * - size: string
 * - disabled: boolean
 * - loading: boolean
 * - icon: string (opcional, ícono antes del texto)
 * - iconRight: string (ícono después)
 * - onClick: function
 * - className: string (adicionales)
 * 
 * Uso:
 * <Button 
 *   variant="primary" 
 *   size="lg" 
 *   icon="⚔️" 
 *   onClick={handleAttack}
 * >
 *   Atacar
 * </Button>
 */
```

#### Input
```javascript
/**
 * Campo de texto reutilizable
 * 
 * Tipos:
 * - text
 * - email
 * - password
 * - number
 * - tel
 * - search
 * 
 * Estados:
 * - normal
 * - focus
 * - error (con mensaje)
 * - disabled
 * 
 * Props:
 * - type: string
 * - placeholder: string
 * - value: string
 * - error: string (mensaje de error)
 * - label: string
 * - icon: string (ícono antes del input)
 * - onInput: function
 * - onFocus: function
 * - onBlur: function
 * - required: boolean
 * - disabled: boolean
 * 
 * Uso:
 * <Input
 *   type="email"
 *   label="Email"
 *   placeholder="tu@email.com"
 *   error={emailError}
 *   onInput={handleEmailChange}
 * />
 */
```

#### Modal
```javascript
/**
 * Modal/Dialog reutilizable
 * 
 * Variantes:
 * - center (centrado en pantalla)
 * - bottom (bottom sheet móvil)
 * - fullscreen (pantalla completa)
 * 
 * Props:
 * - isOpen: boolean
 * - onClose: function
 * - title: string
 * - variant: string
 * - showCloseButton: boolean
 * - closeOnOverlayClick: boolean
 * - closeOnEsc: boolean
 * - children: content
 * 
 * Animaciones:
 * - Fade in overlay
 * - Slide up content (mobile)
 * - Scale in content (desktop)
 * 
 * Uso:
 * <Modal
 *   isOpen={showModal}
 *   onClose={() => setShowModal(false)}
 *   title="Detalle de Territorio"
 *   variant="bottom"
 * >
 *   <TerritoryDetails data={territory} />
 * </Modal>
 */
```

#### Toast
```javascript
/**
 * Notificación toast
 * 
 * Tipos:
 * - success (verde)
 * - error (rojo)
 * - warning (amarillo)
 * - info (azul)
 * 
 * Posiciones:
 * - top-left
 * - top-center
 * - top-right
 * - bottom-left
 * - bottom-center
 * - bottom-right
 * 
 * Props:
 * - type: string
 * - message: string
 * - duration: number (ms, default 3000)
 * - position: string
 * - onClose: function
 * - action: {text, callback} (opcional)
 * 
 * Auto-dismiss después de duration
 * Swipe to dismiss
 * Stack múltiples toasts
 * 
 * Uso:# 📱 Arquitectura Mobile App - Territory Conquest

## 🎯 Visión General

**PWA (Progressive Web App)** construida con:
- HTML5, CSS3, Vanilla JavaScript
- Sin frameworks pesados (React, Vue, etc.)
- Instalable en móvil
- Funciona offline
- Push notifications
- Geolocalización nativa

---

## 📐 Estructura de Carpetas

```
mobile-app/
│
├── index.html                    # Entry point
├── manifest.json                 # PWA manifest
├── service-worker.js             # Service worker para offline
│
├── assets/
│   ├── icons/                    # Iconos PWA (diversos tamaños)
│   │   ├── icon-72x72.png
│   │   ├── icon-96x96.png
│   │   ├── icon-128x128.png
│   │   ├── icon-144x144.png
│   │   ├── icon-152x152.png
│   │   ├── icon-192x192.png
│   │   ├── icon-384x384.png
│   │   └── icon-512x512.png
│   │
│   ├── images/                   # Imágenes de la app
│   │   ├── flags/                # Banderas de países 🇪🇸🇫🇷
│   │   ├── icons/                # Iconos funcionales
│   │   ├── splash/               # Splash screens
│   │   └── backgrounds/          # Fondos de pantallas
│   │
│   └── sounds/                   # Sonidos (conquista, alerta, etc.)
│       ├── conquest.mp3
│       ├── battle.mp3
│       └── alert.mp3
│
├── css/
│   ├── reset.css                 # CSS reset
│   ├── variables.css             # Variables CSS (colores, spacing)
│   ├── animations.css            # Animaciones y transiciones
│   ├── components.css            # Componentes reutilizables
│   ├── layouts.css               # Layouts de páginas
│   ├── map.css                   # Estilos del mapa
│   └── mobile.css                # Responsive mobile-first
│
├── js/
│   │
│   ├── app.js                    # Entry point JS
│   │
│   ├── core/                     # Core de la aplicación
│   │   ├── router.js             # SPA Router
│   │   ├── store.js              # State management (global)
│   │   ├── api.js                # API Client (fetch wrapper)
│   │   ├── auth.js               # Gestión de autenticación
│   │   ├── storage.js            # LocalStorage + IndexedDB
│   │   ├── events.js             # Event bus (pub/sub)
│   │   └── logger.js             # Logging y debug
│   │
│   ├── services/                 # Servicios de negocio
│   │   ├── LocationService.js    # Geolocalización y tracking
│   │   ├── ActivityService.js    # Registro de actividades
│   │   ├── RiskService.js        # Lógica del sistema RISK
│   │   ├── MapService.js         # Gestión del mapa
│   │   ├── NotificationService.js # Push notifications
│   │   ├── SyncService.js        # Sincronización offline
│   │   └── StravaService.js      # Integración Strava
│   │
│   ├── components/               # Componentes UI reutilizables
│   │   ├── base/                 # Componentes base
│   │   │   ├── Button.js
│   │   │   ├── Input.js
│   │   │   ├── Modal.js
│   │   │   ├── Toast.js
│   │   │   ├── Loading.js
│   │   │   ├── Card.js
│   │   │   └── Badge.js
│   │   │
│   │   ├── navigation/           # Navegación
│   │   │   ├── BottomNav.js
│   │   │   ├── TopBar.js
│   │   │   ├── Menu.js
│   │   │   └── Tabs.js
│   │   │
│   │   ├── map/                  # Componentes del mapa
│   │   │   ├── RiskMap.js        # Mapa principal
│   │   │   ├── Hexagon.js        # Hexágono individual
│   │   │   ├── Territory.js      # Territorio
│   │   │   ├── Battle.js         # Indicador de batalla
│   │   │   ├── ZoomControls.js   # Controles zoom
│   │   │   └── Legend.js         # Leyenda del mapa
│   │   │
│   │   ├── activity/             # Actividades
│   │   │   ├── ActivityCard.js
│   │   │   ├── ActivityForm.js
│   │   │   ├── ActivityTracker.js  # Tracking en vivo
│   │   │   ├── RouteMap.js
│   │   │   └── StatsDisplay.js
│   │   │
│   │   ├── conquest/             # Sistema RISK
│   │   │   ├── TerritoryCard.js
│   │   │   ├── BattleCard.js
│   │   │   ├── AttackSlider.js   # Distribuir KM
│   │   │   ├── DefenseIndicator.js
│   │   │   ├── ConquestHistory.js
│   │   │   └── StrategicSuggestion.js
│   │   │
│   │   ├── team/                 # Equipos
│   │   │   ├── TeamCard.js
│   │   │   ├── MemberList.js
│   │   │   ├── TeamStats.js
│   │   │   └── TeamChat.js
│   │   │
│   │   └── profile/              # Perfil usuario
│   │       ├── ProfileHeader.js
│   │       ├── StatsSummary.js
│   │       ├── AchievementsList.js
│   │       └── SettingsPanel.js
│   │
│   ├── pages/                    # Páginas completas (vistas)
│   │   ├── HomePage.js           # Dashboard principal
│   │   ├── MapPage.js            # Mapa RISK completo
│   │   ├── ActivityPage.js       # Lista de actividades
│   │   ├── TrackingPage.js       # Tracking en vivo
│   │   ├── PostActivityPage.js   # Distribuir KM post-entreno
│   │   ├── TeamPage.js           # Vista de equipo
│   │   ├── BattlesPage.js        # Batallas activas
│   │   ├── RankingsPage.js       # Rankings y leaderboards
│   │   ├── ProfilePage.js        # Perfil usuario
│   │   ├── LoginPage.js          # Login
│   │   ├── RegisterPage.js       # Registro
│   │   ├── SettingsPage.js       # Configuración
│   │   └── OnboardingPage.js     # Tutorial inicial
│   │
│   ├── utils/                    # Utilidades
│   │   ├── dom.js                # Helpers DOM
│   │   ├── validators.js         # Validaciones
│   │   ├── formatters.js         # Formato de datos
│   │   ├── calculators.js        # Cálculos (pace, distance, etc)
│   │   ├── animations.js         # Animaciones JS
│   │   ├── geolocation.js        # Utils geo
│   │   └── h3.js                 # H3 client-side
│   │
│   └── lib/                      # Librerías externas
│       ├── leaflet.js            # Mapas (Leaflet)
│       ├── leaflet.css
│       ├── h3-js.js              # H3 para client
│       └── chart.js              # Gráficos (opcional)
│
└── pages/                        # HTML templates
    ├── home.html
    ├── map.html
    ├── activity.html
    ├── tracking.html
    ├── post-activity.html
    ├── team.html
    ├── battles.html
    ├── rankings.html
    ├── profile.html
    ├── login.html
    ├── register.html
    └── settings.html
```

---

## 🏗️ Arquitectura por Capas

### Layer 1: Core (Base)
```
┌─────────────────────────────────────────┐
│           CORE LAYER                    │
│                                         │
│  router.js    store.js    api.js       │
│  auth.js    storage.js   events.js     │
│                                         │
│  Responsable de:                        │
│  - Routing SPA                          │
│  - Estado global                        │
│  - Comunicación con backend             │
│  - Autenticación JWT                    │
│  - Persistencia local                   │
│  - Event bus                            │
└─────────────────────────────────────────┘
```

### Layer 2: Services (Lógica de Negocio)
```
┌─────────────────────────────────────────┐
│         SERVICES LAYER                  │
│                                         │
│  LocationService    ActivityService     │
│  RiskService       MapService          │
│  NotificationService  SyncService      │
│                                         │
│  Responsable de:                        │
│  - Tracking GPS                         │
│  - Gestión de actividades               │
│  - Lógica RISK                          │
│  - Renderizado de mapas                 │
│  - Notificaciones push                  │
│  - Sincronización offline/online        │
└─────────────────────────────────────────┘
```

### Layer 3: Components (UI)
```
┌─────────────────────────────────────────┐
│        COMPONENTS LAYER                 │
│                                         │
│  Base Components (Button, Input, etc)  │
│  Map Components (Hexagon, Territory)   │
│  Activity Components (Tracker, Form)   │
│  Conquest Components (Attack, Battle)  │
│                                         │
│  Responsable de:                        │
│  - Render UI                            │
│  - Interacción usuario                  │
│  - Animaciones visuales                 │
│  - Feedback inmediato                   │
└─────────────────────────────────────────┘
```

### Layer 4: Pages (Vistas Completas)
```
┌─────────────────────────────────────────┐
│           PAGES LAYER                   │
│                                         │
│  HomePage   MapPage   ActivityPage     │
│  TrackingPage   BattlesPage            │
│  ProfilePage   etc...                   │
│                                         │
│  Responsable de:                        │
│  - Composición de componentes           │
│  - Layout de página                     │
│  - Flujos específicos                   │
│  - Gestión de estado de página          │
└─────────────────────────────────────────┘
```

---

## 🔌 Módulos Core Detallados

### 1. router.js - SPA Router
```javascript
/**
 * Router para navegación SPA
 * 
 * Funcionalidades:
 * - Define rutas y componentes asociados
 * - History API (pushState/popState)
 * - Parámetros de ruta (/map/:territoryId)
 * - Query strings (?tab=battles)
 * - Guards (auth required, team required)
 * - Transiciones entre páginas
 * - Deep linking (compartir URLs)
 * - Back button handling
 * 
 * Rutas principales:
 * / → HomePage
 * /map → MapPage
 * /map/:zoom → MapPage con zoom específico
 * /territory/:id → Detalle de territorio
 * /activity → Lista actividades
 * /activity/track → Tracking en vivo
 * /activity/:id/distribute → Distribuir KM
 * /team → Vista equipo
 * /battles → Batallas activas
 * /battle/:id → Detalle batalla
 * /rankings → Rankings
 * /profile → Perfil
 * /login → Login
 * /register → Registro
 * /settings → Configuración
 * 
 * API:
 * Router.navigate(path, params)
 * Router.back()
 * Router.replace(path)
 * Router.on('routeChange', callback)
 */
```

### 2. store.js - State Management
```javascript
/**
 * Store global estilo Redux/Vuex
 * 
 * Estado global:
 * {
 *   user: {
 *     id, username, email,
 *     total_km, total_points, zones_controlled,
 *     team_id, avatar_url
 *   },
 *   
 *   auth: {
 *     isAuthenticated: bool,
 *     token: string,
 *     tokenExpiry: timestamp
 *   },
 *   
 *   map: {
 *     currentZoom: 'world'|'country'|'region'|'city',
 *     territories: [],
 *     selectedTerritory: object,
 *     filters: {
 *       showOnlyMine: bool,
 *       showBattles: bool,
 *       showTeam: bool
 *     }
 *   },
 *   
 *   tracking: {
 *     isActive: bool,
 *     currentActivity: {
 *       startTime, distance, duration,
 *       route: [], currentLocation
 *     },
 *     isPaused: bool
 *   },
 *   
 *   battles: {
 *     active: [],
 *     userRelated: [],
 *     critical: []
 *   },
 *   
 *   notifications: {
 *     unread: number,
 *     items: []
 *   },
 *   
 *   offline: {
 *     isOnline: bool,
 *     pendingSync: [],
 *     lastSync: timestamp
 *   },
 *   
 *   ui: {
 *     loading: bool,
 *     modal: null,
 *     toast: null,
 *     bottomNav: 'visible'|'hidden'
 *   }
 * }
 * 
 * API:
 * Store.getState()
 * Store.setState(path, value)
 * Store.subscribe(path, callback)
 * Store.dispatch(action, payload)
 * Store.reset()
 */
```

### 3. api.js - API Client
```javascript
/**
 * Cliente HTTP para comunicación con backend
 * 
 * Funcionalidades:
 * - Wrapper de fetch()
 * - Interceptores de request/response
 * - Refresh token automático
 * - Retry con exponential backoff
 * - Queue de requests offline
 * - Timeout configurable
 * - Cache de responses
 * - Error handling centralizado
 * 
 * Endpoints agrupados:
 * API.auth.login(email, password)
 * API.auth.register(data)
 * API.auth.logout()
 * API.auth.refreshToken()
 * 
 * API.user.getProfile()
 * API.user.updateProfile(data)
 * API.user.getStats()
 * 
 * API.activities.list(params)
 * API.activities.create(data)
 * API.activities.delete(id)
 * 
 * API.risk.getMap(zoom)
 * API.risk.getTerritory(id)
 * API.risk.executeMove(data)
 * API.risk.getBattles()
 * API.risk.previewAttack(territoryId, units)
 * 
 * API.teams.list()
 * API.teams.create(data)
 * API.teams.join(id)
 * API.teams.leave()
 * 
 * API.leaderboard.users(metric)
 * API.leaderboard.teams(metric)
 * 
 * Config:
 * API.setBaseURL(url)
 * API.setToken(token)
 * API.setTimeout(ms)
 */
```

### 4. auth.js - Authentication Manager
```javascript
/**
 * Gestión de autenticación
 * 
 * Funcionalidades:
 * - Login/Register
 * - Guardar/Leer token JWT
 * - Refresh token automático
 * - Verificar expiración
 * - Logout y limpieza
 * - Redirect a login si no autenticado
 * - Persistencia de sesión
 * 
 * Flujo:
 * 1. Usuario hace login → Guarda token
 * 2. Todas las requests llevan token en header
 * 3. Si 401 → Intenta refresh token
 * 4. Si refresh falla → Redirect a login
 * 5. Al logout → Limpia token y store
 * 
 * API:
 * Auth.login(email, password)
 * Auth.register(data)
 * Auth.logout()
 * Auth.isAuthenticated()
 * Auth.getToken()
 * Auth.refreshToken()
 * Auth.requireAuth(callback)
 */
```

### 5. storage.js - Persistent Storage
```javascript
/**
 * Abstracción de almacenamiento
 * 
 * Capas:
 * 1. LocalStorage - Datos simples (settings, token)
 * 2. IndexedDB - Datos grandes (activities offline, map tiles)
 * 3. Cache API - Assets estáticos
 * 
 * Stores en IndexedDB:
 * - activities (actividades offline)
 * - territories (cache de territorios)
 * - mapTiles (tiles del mapa)
 * - syncQueue (pending operations)
 * 
 * API:
 * Storage.set(key, value)
 * Storage.get(key)
 * Storage.remove(key)
 * Storage.clear()
 * 
 * Storage.db.activities.add(data)
 * Storage.db.activities.getAll()
 * Storage.db.activities.delete(id)
 * 
 * Storage.cache.put(url, response)
 * Storage.cache.match(url)
 */
```

### 6. events.js - Event Bus
```javascript
/**
 * Sistema de eventos pub/sub
 * 
 * Eventos principales:
 * - auth:login
 * - auth:logout
 * - auth:expired
 * 
 * - activity:started
 * - activity:paused
 * - activity:resumed
 * - activity:completed
 * - activity:created
 * 
 * - tracking:locationUpdate
 * - tracking:distanceUpdate
 * 
 * - conquest:territoryGained
 * - conquest:territoryLost
 * - conquest:battleStarted
 * - conquest:battleEnded
 * 
 * - network:online
 * - network:offline
 * - sync:completed
 * 
 * - notification:received
 * - notification:clicked
 * 
 * API:
 * Events.on(event, callback)
 * Events.off(event, callback)
 * Events.emit(event, data)
 * Events.once(event, callback)
 */
```

---

## 🎨 Sistema de Componentes

### Patrón de Componente Base
```javascript
/**
 * Todos los componentes siguen este patrón:
 * 
 * class ComponentName {
 *   constructor(props) {
 *     this.props = props;
 *     this.state = {};
 *     this.element = null;
 *   }
 *   
 *   render() {
 *     // Retorna HTML string o DOM element
 *   }
 *   
 *   mount(container) {
 *     // Renderiza y agrega al DOM
 *   }
 *   
 *   update(newProps) {
 *     // Actualiza props y re-renderiza
 *   }
 *   
 *   destroy() {
 *     // Limpieza de event listeners, etc
 *   }
 *   
 *   // Event handlers
 *   handleClick() { }
 *   handleChange() { }
 * }
 */
```

---

## 📱 Páginas Principales Detalladas

### 1. HomePage (Dashboard)
```
┌─────────────────────────────────────────┐
│  [≡]  Territory Conquest     [🔔3]     │  ← TopBar
├─────────────────────────────────────────┤
│                                         │
│  👤 runner_bcn            #1,234 🇪🇸   │  ← ProfileHeader
│  156 km | 1,567 pts | 12 zonas        │
│                                         │
├─────────────────────────────────────────┤
│  ⚠️ ALERTAS CRÍTICAS                   │
│  ┌───────────────────────────────────┐ │
│  │ 🔴 Francia conquista Pirineos    │ │
│  │ Se necesitan 50 unidades YA      │ │
│  │ [DEFENDER AHORA]                 │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ 🟠 Badalona contraataca          │ │
│  │ -5 hexágonos perdidos            │ │
│  │ [VER BATALLA]                    │ │
│  └───────────────────────────────────┘ │
├─────────────────────────────────────────┤
│  📊 TU SITUACIÓN                       │
│  ┌───────────────────────────────────┐ │
│  │ 🇪🇸 ESPAÑA                        │ │
│  │ Territorios: 45 (#4 mundial)     │ │
│  │ Bajo ataque: 3 ⚠️                │ │
│  └───────────────────────────────────┘ │
│  ┌───────────────────────────────────┐ │
│  │ 🏴 CATALUÑA                        │ │
│  │ Unidades: 456                     │ │
│  │ Estado: 🔴 BATALLA ACTIVA        │ │
│  │ Francia: 58% vs 42% ⚠️⚠️        │ │
│  └───────────────────────────────────┘ │
├─────────────────────────────────────────┤
│  🏆 LOGROS RECIENTES                   │
│  [🏅 Conquistador] [⭐ 10K Runner]   │
├─────────────────────────────────────────┤
│  [🏃 Iniciar]  [🗺️ Mapa]  [👥 Team]   │  ← Quick Actions
└─────────────────────────────────────────┘
│  [🏠] [🗺️] [➕] [⚔️] [👤]              │  ← BottomNav
└─────────────────────────────────────────┘

Componentes:
- TopBar (notifications badge)
- ProfileHeader
- AlertsList (priority ordered)
- SituationSummary
- AchievementsBanner
- QuickActions
- BottomNav

State local:
- alerts: []
- userStats: {}
- recentAchievements: []

Interacciones:
- Pull to refresh
- Tap alerta → Navega a detalle
- Tap situación → Navega a mapa
- Tap "Iniciar" → TrackingPage
```

### 2. MapPage (Mapa RISK)
```
┌─────────────────────────────────────────┐
│  [←]  Mapa Mundial         [⚙️]        │  ← TopBar con back
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │                                 │   │
│  │        🗺️ MAPA INTERACTIVO      │   │
│  │                                 │   │
│  │  [Zoom: Mundial ▼]              │   │
│  │                                 │   │
│  │   ╔═══════════════╗             │   │
│  │   ║    FRANCIA    ║             │   │
│  │   ║               ║             │   │
│  │   ║    🇫🇷 ⚔️ 42  ║             │   │
│  │   ╚═══════════════╝             │   │
│  │            ║                     │   │
│  │   ╔════════╩═════════╗          │   │
│  │   ║     ESPAÑA       ║          │   │
│  │   ║                  ║          │   │
│  │   ║    🇪🇸  156      ║          │   │
│  │   ╚══════════════════╝          │   │
│  │                                 │   │
│  │  [+] [-] [📍] [🎯]              │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Leyenda:                               │
│  🇪🇸 Tu país  🇫🇷 Enemigo  ⚔️ Batalla  │
│  [Filtros ▼]                            │
└─────────────────────────────────────────┘

Niveles de zoom:
1. Mundial → Continentes/Países
2. Continental → Países
3. País → Regiones
4. Regional → Ciudades
5. Ciudad → Distritos/Barrios
6. Barrio → Hexágonos individuales

Interacciones:
- Pinch to zoom
- Tap territorio → Modal con detalles
- Long press territorio → Opciones (atacar, ver historia)
- Swipe entre niveles
- Double tap → Zoom in
- Pan para mover mapa

Componentes:
- MapCanvas (Leaflet)
- ZoomControls
- TerritoryLayer (hexágonos coloreados)
- BattleMarkers (animados)
- Legend
- FilterPanel
- TerritoryModal (detalle al tap)

State local:
- currentZoom: 'world'
- territories: []
- selectedTerritory: null
- filters: {}
- mapCenter: {lat, lng}
```

### 3. TrackingPage (Tracking en Vivo)
```
┌─────────────────────────────────────────┐
│  [✕]  Entrenamiento            [🔊]    │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │                                 │   │
│  │    📍 MAPA DE RUTA EN VIVO      │   │
│  │                                 │   │
│  │    •─────────────•              │   │
│  │   Inicio      Tu posición       │   │
│  │                                 │   │
│  │  Hexágonos atravesados: 8       │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      5.2 km                     │   │  ← Distancia grande
│  │                                 │   │
│  │  23:45                4'32"/km  │   │  ← Tiempo | Pace
│  │  245 kcal              ▲ 45m    │   │  ← Calorías | Elevación
│  └─────────────────────────────────┘   │
│                                         │
│  [  ||  PAUSAR  ]                      │   │  ← Botón principal
│  [  ⏹  TERMINAR  ]                     │   │
│                                         │
│  💾 Auto-guardando cada 30 seg...      │
└─────────────────────────────────────────┘

Estados:
- Tracking (grabando GPS)
- Paused (pausado)
- Stopped (terminado)

Funcionalidades:
- GPS tracking cada 5 segundos
- Cálculo distancia en tiempo real
- Detección automática de hexágonos
- Guardar offline si no hay conexión
- Notificaciones cada 1km
- Lock screen controls (PWA)
- Vibración al pausar/reanudar

Componentes:
- LiveMap (ruta en tiempo real)
- StatsDisplay (grande y legible)
- ControlButtons
- HexagonCounter
- AutoSaveIndicator

State local:
- isTracking: bool
- isPaused: bool
- currentActivity: {
    startTime, distance, duration,
    route: [{lat, lng, timestamp}],
    hexagons: Set,
    pace, calories, elevation
  }
```

### 4. PostActivityPage (Distribución de KM)
```
┌─────────────────────────────────────────┐
│  [←]  ¡10 KM COMPLETADOS! 🎉          │
├─────────────────────────────────────────┤
│  DEFENSA AUTOMÁTICA ✅                 │
│  ├─ 🇪🇸 España: +10 km                 │
│  ├─ 🏴 Cataluña: +10 km                │
│  └─ 📍 Barcelona: +10 km               │
│                                         │
├─────────────────────────────────────────┤
│  🎯 ¿DÓNDE ATACAR? (10 unidades)       │
│                                         │
│  [ 🗺️ VER MAPA PARA SELECCIONAR ]      │
│                                         │
│  SUGERENCIAS:                           │
│  ┌───────────────────────────────────┐ │
│  │ 🔴 CRÍTICO                        │ │
│  │ FRONTERA PIRINEOS                 │ │
│  │ Francia ganando (+8% hoy)         │ │
│  │                                   │ │
│  │ ████████░░ 8 un