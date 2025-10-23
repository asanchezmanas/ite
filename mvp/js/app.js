// js/app.js

// Core
import Router from './core/router.js';
import Store from './core/store.js';
import Auth from './core/auth.js';

// Pages
import LoginPage from './pages/login.js';
import HomePage from './pages/home.js';
import TrackingPage from './pages/tracking.js';
import PostActivityPage from './pages/post-activity.js';
import MapPage from './pages/map.js';
import BattlesPage from './pages/battles.js';
import ProfilePage from './pages/profile.js';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  // Setup router
  Router.addRoute('/', HomePage, { requiresAuth: true });
  Router.addRoute('/login', LoginPage);
  Router.addRoute('/tracking', TrackingPage, { requiresAuth: true });
  Router.addRoute('/activity/:id/distribute', PostActivityPage, { requiresAuth: true });
  Router.addRoute('/map', MapPage, { requiresAuth: true });
  Router.addRoute('/battles', BattlesPage, { requiresAuth: true });
  Router.addRoute('/profile', ProfilePage, { requiresAuth: true });
  
  // Start
  Router.init();
  
  // Register service worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js');
  }
});
