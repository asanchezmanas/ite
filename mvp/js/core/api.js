// js/core/api.js

import Store from './store.js';

class APIClass {
  constructor() {
    this.baseURL = 'https://your-backend.onrender.com/api';
  }
  
  async request(endpoint, options = {}) {
    const token = Store.getState('auth.token');
    
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers
      }
    };
    
    const response = await fetch(`${this.baseURL}${endpoint}`, config);
    
    if (!response.ok) {
      if (response.status === 401) {
        Store.setState('auth.isAuthenticated', false);
        window.location.href = '/login';
      }
      throw new Error(`HTTP ${response.status}`);
    }
    
    return response.json();
  }
  
  // Auth
  auth = {
    login: (email, password) => 
      this.request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      }),
    
    register: (data) =>
      this.request('/auth/register', {
        method: 'POST',
        body: JSON.stringify(data)
      })
  };
  
  // Activities
  activities = {
    create: (data) =>
      this.request('/activities', {
        method: 'POST',
        body: JSON.stringify(data)
      }),
    
    list: () => this.request('/activities/me')
  };
  
  // RISK
  risk = {
    getMap: (zoom = 'city', lat = 41.3851, lng = 2.1734) =>
      this.request(`/risk/map?zoom=${zoom}&lat=${lat}&lng=${lng}`),
    
    executeMove: (data) =>
      this.request('/risk/move', {
        method: 'POST',
        body: JSON.stringify(data)
      }),
    
    getBattles: () => this.request('/risk/battles')
  };
  
  // User
  user = {
    getProfile: () => this.request('/users/me'),
    getStats: () => this.request('/users/me/stats')
  };
}

export default new APIClass();
