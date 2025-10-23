//  js/core/store.js

class StoreClass {
  constructor() {
    this.state = {
      auth: {
        isAuthenticated: false,
        token: null,
        user: null
      },
      tracking: {
        isActive: false,
        currentActivity: null
      },
      map: {
        territories: [],
        battles: []
      }
    };
    
    this.listeners = new Map();
    this.restoreFromStorage();
  }
  
  setState(path, value) {
    const keys = path.split('.');
    const lastKey = keys.pop();
    const parent = keys.reduce((obj, key) => obj[key], this.state);
    parent[lastKey] = value;
    
    this.notify(path);
    this.saveToStorage();
  }
  
  getState(path) {
    return path.split('.').reduce((obj, key) => obj?.[key], this.state);
  }
  
  subscribe(path, callback) {
    if (!this.listeners.has(path)) {
      this.listeners.set(path, new Set());
    }
    this.listeners.get(path).add(callback);
    
    return () => this.listeners.get(path).delete(callback);
  }
  
  notify(path) {
    const callbacks = this.listeners.get(path);
    if (callbacks) {
      const value = this.getState(path);
      callbacks.forEach(cb => cb(value));
    }
  }
  
  saveToStorage() {
    localStorage.setItem('store', JSON.stringify(this.state));
  }
  
  restoreFromStorage() {
    const saved = localStorage.getItem('store');
    if (saved) {
      this.state = JSON.parse(saved);
    }
  }
}

export default new StoreClass();
