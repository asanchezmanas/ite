# ite

# Territory Conquest - Frontend

Progressive Web App para gamificación deportiva con conquista territorial.

## 🚀 Quick Start

### Desarrollo Local
````bash
# Opción 1: Python
python -m http.server 8080

# Opción 2: Node
npx http-server -p 8080

# Opción 3: PHP
php -S localhost:8080
````

Abrir: http://localhost:8080

### Configuración

Editar API URL en `js/core/api.js`:
````javascript
this.baseURL = 'http://localhost:8000/api'; // Local
// this.baseURL = 'https://tu-api.onrender.com/api'; // Producción
````

## 📱 Estructura
````
├── index.html              # Entry point
├── manifest.json           # PWA config
├── service-worker.js       # Offline support
├── css/
│   └── style.css          # Styles (TailAdmin inspired)
├── js/
│   ├── app.js             # Initialize app
│   ├── core/              # Router, Store, API, Auth
│   ├── services/          # Location, Map, Analytics
│   └── pages/             # 11 pages
└── assets/
    └── icons/             # PWA icons
````

## 🧪 Testing

Ver `TESTING.md` para checklist completo.

### Test Rápido

1. Crear usuario
2. Iniciar tracking GPS
3. Caminar 100m
4. Verificar distancia ~0.1 km
5. Terminar y distribuir KM
6. Ver en mapa

## 🚀 Deploy

Ver `DEPLOY.md` para instrucciones completas.

### Deploy Rápido a Render
````bash
# 1. Push a GitHub
git push origin main

# 2. Render → New Static Site
# 3. Connect repo
# 4. Build: echo "No build"
# 5. Publish: .
# 6. Deploy!
````

## 🎨 Personalización

### Colores

Editar `css/style.css`:
````css
:root {
  --brand-500: #465fff;  /* Color principal */
  --brand-600: #3641f5;  /* Hover */
}
````

### Features

Habilitar/deshabilitar en `js/app.js`:
````javascript
const FEATURES = {
  PREMIUM: true,
  TEAMS: true,
  STRAVA: false  // Requiere API key
};
````

## 📊 Analytics

Events se trackean automáticamente. Ver en consola:
````javascript
📊 Analytics: page_view { page_name: "home" }
📊 Analytics: activity_completed { distance_km: 10 }
````

## 🐛 Debug

### Service Worker
````javascript
// Desregistrar
navigator.serviceWorker.getRegistrations()
  .then(regs => regs.forEach(reg => reg.unregister()));

// Hard refresh
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)
````

### GPS
````javascript
// Verificar permisos
navigator.permissions.query({name:'geolocation'})
  .then(result => console.log(result.state));
````

## 📚 Docs

- [Developer Guide](DEVELOPER_GUIDE.md) - Para nuevos devs
- [Testing Checklist](TESTING.md) - QA completo
- [Deploy Guide](DEPLOY.md) - Paso a paso producción

## 🤝 Contributing

1. Fork repo
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

## 📄 License


