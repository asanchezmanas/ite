// js/core/router.js

class RouterClass {
  constructor() {
    this.routes = new Map();
    this.currentPage = null;
  }
  
  addRoute(path, PageClass, options = {}) {
    this.routes.set(path, { PageClass, options });
  }
  
  init() {
    // Handle navigation
    window.addEventListener('popstate', () => this.handleRoute());
    
    // Intercept clicks
    document.addEventListener('click', (e) => {
      if (e.target.matches('[href^="/"]')) {
        e.preventDefault();
        this.navigate(e.target.getAttribute('href'));
      }
    });
    
    // Initial route
    this.handleRoute();
  }
  
  async handleRoute() {
    const path = window.location.pathname;
    const route = this.findRoute(path);
    
    if (!route) {
      this.navigate('/');
      return;
    }
    
    // Check auth
    if (route.options.requiresAuth && !Store.state.auth.isAuthenticated) {
      this.navigate('/login');
      return;
    }
    
    // Cleanup previous page
    if (this.currentPage?.destroy) {
      this.currentPage.destroy();
    }
    
    // Render new page
    const container = document.getElementById('app');
    this.currentPage = new route.PageClass();
    await this.currentPage.render(container);
    
    // Update bottom nav
    this.updateBottomNav(path);
  }
  
  findRoute(path) {
    // Exact match
    if (this.routes.has(path)) {
      return this.routes.get(path);
    }
    
    // Param match
    for (let [routePath, route] of this.routes) {
      if (routePath.includes(':')) {
        const regex = new RegExp('^' + routePath.replace(/:\w+/g, '([^/]+)') + '$');
        if (regex.test(path)) {
          return route;
        }
      }
    }
    
    return null;
  }
  
  navigate(path) {
    window.history.pushState({}, '', path);
    this.handleRoute();
  }
  
  updateBottomNav(path) {
    document.querySelectorAll('#bottom-nav a').forEach(link => {
      link.classList.toggle('active', link.getAttribute('href') === path);
    });
  }
}

export default new RouterClass();
