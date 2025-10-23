// js/pages/login.js
import Store from '../core/store.js';
import API from '../core/api.js';
import Auth from '../core/auth.js';

export default class LoginPage {
  constructor() {
    this.isLogin = true; // true = login, false = register
  }
  
  async render(container) {
    container.innerHTML = `
      <div class="login-page" style="min-height: 100vh; display: flex; flex-direction: column; justify-content: center; padding: 24px; background: var(--bg-primary);">
        <!-- Logo -->
        <div style="text-align: center; margin-bottom: 48px;">
          <div style="width: 80px; height: 80px; margin: 0 auto 16px; background: var(--brand-500); border-radius: var(--radius-xl); display: flex; align-items: center; justify-content: center; font-size: 40px;">
            🗺️
          </div>
          <h1 style="margin-bottom: 8px;">Territory Conquest</h1>
          <p class="text-secondary">Conquista el mundo corriendo</p>
        </div>
        
        <!-- Form Card -->
        <div class="card" style="max-width: 400px; margin: 0 auto; width: 100%;">
          <div style="text-align: center; margin-bottom: 24px;">
            <h2 id="form-title">${this.isLogin ? 'Iniciar Sesión' : 'Crear Cuenta'}</h2>
            <p class="text-sm text-secondary" style="margin-top: 8px;">
              ${this.isLogin ? '¿No tienes cuenta?' : '¿Ya tienes cuenta?'}
              <a href="#" id="toggle-mode" style="color: var(--brand-500); text-decoration: none; font-weight: 500;">
                ${this.isLogin ? 'Regístrate' : 'Inicia sesión'}
              </a>
            </p>
          </div>
          
          <form id="auth-form">
            <!-- Username (only for register) -->
            <div id="username-group" style="margin-bottom: 16px; display: ${this.isLogin ? 'none' : 'block'};">
              <label style="display: block; margin-bottom: 6px; font-size: 14px; font-weight: 500;">
                Nombre de usuario
              </label>
              <input 
                type="text" 
                id="username" 
                name="username"
                class="input" 
                placeholder="runner_bcn"
                ${!this.isLogin ? 'required' : ''}
              >
            </div>
            
            <!-- Email -->
            <div style="margin-bottom: 16px;">
              <label style="display: block; margin-bottom: 6px; font-size: 14px; font-weight: 500;">
                Email
              </label>
              <input 
                type="email" 
                id="email" 
                name="email"
                class="input" 
                placeholder="tu@email.com"
                required
                autocomplete="email"
              >
            </div>
            
            <!-- Password -->
            <div style="margin-bottom: 16px;">
              <label style="display: block; margin-bottom: 6px; font-size: 14px; font-weight: 500;">
                Contraseña
              </label>
              <input 
                type="password" 
                id="password" 
                name="password"
                class="input" 
                placeholder="••••••••"
                required
                autocomplete="${this.isLogin ? 'current-password' : 'new-password'}"
              >
              ${!this.isLogin ? '<p class="text-xs text-secondary" style="margin-top: 4px;">Mínimo 8 caracteres</p>' : ''}
            </div>
            
            <!-- Remember me (login only) -->
            ${this.isLogin ? `
              <div style="display: flex; align-items: center; margin-bottom: 24px;">
                <input 
                  type="checkbox" 
                  id="remember" 
                  style="margin-right: 8px; width: 16px; height: 16px; cursor: pointer;"
                >
                <label for="remember" style="font-size: 14px; cursor: pointer;">
                  Recordarme
                </label>
              </div>
            ` : ''}
            
            <!-- Error message -->
            <div id="error-message" style="display: none; padding: 12px; background: var(--error-50); border-left: 4px solid var(--error-500); border-radius: var(--radius-md); margin-bottom: 16px;">
              <p class="text-sm" style="color: var(--error-500);"></p>
            </div>
            
            <!-- Submit button -->
            <button 
              type="submit" 
              id="submit-btn"
              class="btn btn-primary btn-large"
            >
              ${this.isLogin ? 'Iniciar Sesión' : 'Crear Cuenta'}
            </button>
            
            ${this.isLogin ? `
              <a href="#" id="forgot-password" style="display: block; text-align: center; margin-top: 16px; color: var(--brand-500); text-decoration: none; font-size: 14px;">
                ¿Olvidaste tu contraseña?
              </a>
            ` : ''}
          </form>
        </div>
        
        <!-- Demo credentials (development only) -->
        <div class="card" style="max-width: 400px; margin: 24px auto 0; width: 100%; background: var(--bg-secondary); border: 1px dashed var(--border-color);">
          <p class="text-xs text-secondary" style="text-align: center; margin-bottom: 8px;">
            🧪 Credenciales de prueba:
          </p>
          <p class="text-xs" style="text-align: center;">
            <strong>Email:</strong> demo@territoryconquest.com<br>
            <strong>Password:</strong> demo1234
          </p>
        </div>
      </div>
    `;
    
    this.attachEvents();
  }
  
  attachEvents() {
    // Toggle between login/register
    document.getElementById('toggle-mode').addEventListener('click', (e) => {
      e.preventDefault();
      this.isLogin = !this.isLogin;
      this.render(document.getElementById('app'));
    });
    
    // Form submit
    document.getElementById('auth-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      await this.handleSubmit();
    });
    
    // Forgot password
    document.getElementById('forgot-password')?.addEventListener('click', (e) => {
      e.preventDefault();
      alert('Función de recuperación de contraseña en desarrollo');
    });
  }
  
  async handleSubmit() {
    const submitBtn = document.getElementById('submit-btn');
    const errorMsg = document.getElementById('error-message');
    
    // Get form data
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const username = document.getElementById('username')?.value.trim();
    
    // Validate
    if (!email || !password) {
      this.showError('Por favor completa todos los campos');
      return;
    }
    
    if (!this.isLogin && !username) {
      this.showError('El nombre de usuario es requerido');
      return;
    }
    
    if (password.length < 8) {
      this.showError('La contraseña debe tener al menos 8 caracteres');
      return;
    }
    
    // Hide error
    errorMsg.style.display = 'none';
    
    // Loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="loading"></span> Cargando...';
    
    try {
      if (this.isLogin) {
        // Login
        const response = await API.auth.login(email, password);
        await Auth.handleLoginSuccess(response);
        
      } else {
        // Register
        const response = await API.auth.register({
          email,
          username,
          password
        });
        await Auth.handleLoginSuccess(response);
      }
      
      // Redirect to home
      window.location.href = '/';
      
    } catch (error) {
      console.error('Auth error:', error);
      
      let message = 'Error al ' + (this.isLogin ? 'iniciar sesión' : 'registrarse');
      
      if (error.message.includes('401')) {
        message = 'Email o contraseña incorrectos';
      } else if (error.message.includes('409')) {
        message = 'Este email ya está registrado';
      } else if (error.message.includes('Network')) {
        message = 'Error de conexión. Verifica tu internet.';
      }
      
      this.showError(message);
      
      // Reset button
      submitBtn.disabled = false;
      submitBtn.textContent = this.isLogin ? 'Iniciar Sesión' : 'Crear Cuenta';
    }
  }
  
  showError(message) {
    const errorMsg = document.getElementById('error-message');
    errorMsg.querySelector('p').textContent = message;
    errorMsg.style.display = 'block';
    
    // Scroll to error
    errorMsg.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
  
  destroy() {
    // Cleanup
  }
}
