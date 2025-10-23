// js/core/auth.js
import Store from './store.js';
import API from './api.js';

class AuthClass {
  constructor() {
    this.TOKEN_KEY = 'auth_token';
    this.USER_KEY = 'user_data';
  }
  
  async handleLoginSuccess(response) {
    const { access_token, token_type, user } = response;
    
    // Save token
    localStorage.setItem(this.TOKEN_KEY, access_token);
    
    // Save user
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    
    // Update store
    Store.setState('auth.isAuthenticated', true);
    Store.setState('auth.token', access_token);
    Store.setState('user', user);
    
    // Set token in API client
    API.setToken(access_token);
  }
  
  async logout() {
    // Clear storage
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    
    // Clear store
    Store.setState('auth.isAuthenticated', false);
    Store.setState('auth.token', null);
    Store.setState('user', null);
    
    // Redirect to login
    window.location.href = '/login';
  }
  
  isAuthenticated() {
    return Store.getState('auth.isAuthenticated');
  }
  
  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  }
  
  getUser() {
    const userStr = localStorage.getItem(this.USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  }
  
  // Check if token is valid (basic check)
  async checkAuth() {
    const token = this.getToken();
    if (!token) return false;
    
    try {
      // Try to get profile
      const user = await API.user.getProfile();
      Store.setState('user', user);
      Store.setState('auth.isAuthenticated', true);
      return true;
    } catch (error) {
      // Token invalid, clear everything
      this.logout();
      return false;
    }
  }
}

export default new AuthClass();
