// js/pages/settings.js
import Store from '../core/store.js';
import API from '../core/api.js';
import Analytics from '../core/analytics.js';

export default class SettingsPage {
  constructor() {
    this.user = null;
    this.settings = {
      notifications: true,
      gps_tracking: true,
      auto_sync: true,
      dark_mode: false
    };
  }
  
  async render(container) {
    await this.loadSettings();
    
    container.innerHTML = `
      <div class="settings-page">
        <!-- Top Bar -->
        <div class="top-bar">
          <button class="btn-back" onclick="window.history.back()">←</button>
          <h1>Configuración</h1>
        </div>
        
        <!-- Account Section -->
        <div style="padding: 16px;">
          <h3 style="margin-bottom: 12px;">👤 Cuenta</h3>
          
          <div class="card" style="margin-bottom: 16px;">
            <div class="setting-item">
              <div>
                <div style="font-weight: 500;">Email</div>
                <div class="text-sm text-secondary">${this.user?.email}</div>
              </div>
              <button class="btn btn-secondary btn-sm">Cambiar</button>
            </div>
            
            <div style="border-top: 1px solid var(--border-color); margin: 12px 0;"></div>
            
            <div class="setting-item">
              <div>
                <div style="font-weight: 500;">Contraseña</div>
                <div class="text-sm text-secondary">••••••••</div>
              </div>
              <button class="btn btn-secondary btn-sm">Cambiar</button>
            </div>
          </div>
        </div>
        
        <!-- Privacy Section -->
        <div style="padding: 0 16px 16px;">
          <h3 style="margin-bottom: 12px;">🔒 Privacidad</h3>
          
          <div class="card">
            <div class="setting-item">
              <div>
                <div style="font-weight: 500;">Perfil público</div>
                <div class="text-sm text-secondary">Otros pueden ver tu perfil</div>
              </div>
              <label class="switch">
                <input type="checkbox" id="public-profile" checked>
                <span class="slider"></span>
              </label>
            </div>
            
            <div style="border-top: 1px solid var(--border-color); margin: 12px 0;"></div>
            
            <div class="setting-item">
              <div>
                <div style="font-weight: 500;">Mostrar ubicación</div>
                <div class="text-sm text-secondary">En actividades y mapa</div>
              </div>
              <label class="switch">
                <input type="checkbox" id="show-location" checked>
                <span class="slider"></span>
              </label>
            </div>
          </div>
        </div>
        
        <!-- Notifications Section -->
        <div style="padding: 0 16px 16px;">
          <h3 style="margin-bottom: 12px;">🔔 Notificaciones</h3>
          
          <div class="card">
            <div class="setting-item">
              <div>
                <div style="font-weight: 500;">Push notifications</div>
                <div class="text-sm text-secondary">Alertas en tiempo real</div>
              </div>
              <label class="switch">
                <input type="checkbox" id="push-notifications" ${this.settings.notifications ? 'checked' : ''}>
                <span class="slider"></span>
              </label>
            </div>
            
            <div style="border-top: 1px solid var(--border-color); margin: 12px 0;"></div>
            
            <div class="setting-item">
              <div>
                <div style="font-weight: 500;">Batallas críticas</div>
                <div class="text-sm text-secondary">Cuando tus territorios están en riesgo</div>
              </div>
              <label class="switch">
                <input type="checkbox" id="battle-alerts" checked>
                <span class="slider"></span>
              </label>
            </div>
            
            <div style="border-top: 1px solid var(--border-color); margin: 12px 0;"></div>
            
            <div class="setting-item">
              <div>
                <div style="font-weight: 500;">Logros</div>
                <div class="text-sm text-secondary">Cuando desbloqueas logros</div>
              </div>
              <label class="switch">
                <input type="checkbox" id="achievement-alerts" checked>
                <span class="slider"></span>
              </label>
            </div>
          </div>
        </div>
        
        <!-- App Settings -->
        <div style="padding: 0 16px 16px;">
          <h3 style="margin-bottom: 12px;">⚙️ Aplicación</h3>
          
          <div class="card">
            <div class="setting-item">
              <div>
                <div style="font-weight: 500;">Modo oscuro</div>
                <div class="text-sm text-secondary">Tema de la aplicación</div>
              </div>
              <label class="switch">
                <input type="checkbox" id="dark-mode" ${this.settings.dark_mode ? 'checked' : ''}>
                <span class="slider"></span>
              </label>
            </div>
            
            <div style="border-top: 1px solid var(--border-color); margin: 12px 0;"></div>
            
            <div class="setting-item">
              <div>
                <div style="font-weight: 500;">Sincronización automática</div>
                <div class="text-sm text-secondary">Con Strava y otros servicios</div>
              </div>
              <label class="switch">
                <input type="checkbox" id="auto-sync" ${this.settings.auto_sync ? 'checked' : ''}>
                <span class="slider"></span>
              </label>
            </div>
            
            <div style="border-top: 1px solid var(--border-color); margin: 12px 0;"></div>
            
            <div class="setting-item">
              <div>
                <div style="font-weight: 500;">Seguimiento GPS</div>
                <div class="text-sm text-secondary">Precisión de ubicación</div>
              </div>
              <select class="input" style="width: auto; padding: 8px 12px;" id="gps-accuracy">
                <option value="high">Alta</option>
                <option value="medium" selected>Media</option>
                <option value="low">Baja</option>
              </select>
            </div>
          </div>
        </div>
        
        <!-- Integrations -->
        <div style="padding: 0 16px 16px;">
          <h3 style="margin-bottom: 12px;">🔗 Integraciones</h3>
          
          <div class="card">
            <div class="setting-item">
              <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 40px; height: 40px; background: #FC4C02; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; color: white; font-weight: 700;">
                  S
                </div>
                <div>
                  <div style="font-weight: 500;">Strava</div>
                  <div class="text-sm text-secondary">No conectado</div>
                </div>
              </div>
              <button class="btn btn-primary btn-sm">Conectar</button>
            </div>
          </div>
        </div>
        
        <!-- Data -->
        <div style="padding: 0 16px 16px;">
          <h3 style="margin-bottom: 12px;">📦 Datos</h3>
          
          <div class="card">
            <button class="setting-item" style="width: 100%; border: none; background: none; padding: 0; cursor: pointer;">
              <div>
                <div style="font-weight: 500;">Exportar datos</div>
                <div class="text-sm text-secondary">Descarga tus actividades</div>
              </div>
              <span style="font-size: 20px;">→</span>
            </button>
            
            <div style="border-top: 1px solid var(--border-color); margin: 12px 0;"></div>
            
            <button class="setting-item" style="width: 100%; border: none; background: none; padding: 0; cursor: pointer;">
              <div>
                <div style="font-weight: 500; color: var(--error-500);">Eliminar cuenta</div>
                <div class="text-sm text-secondary">Acción permanente</div>
              </div>
              <span style="font-size: 20px; color: var(--error-500);">→</span>
            </button>
          </div>
        </div>
        
        <!-- About -->
        <div style="padding: 0 16px 32px; text-align: center;">
          <p class="text-sm text-secondary">Territory Conquest v1.0.0</p>
          <p class="text-xs text-secondary" style="margin-top: 4px;">
            <a href="/terms" style="color: var(--brand-500); text-decoration: none;">Términos</a> • 
            <a href="/privacy" style="color: var(--brand-500); text-decoration: none;">Privacidad</a> • 
            <a href="/support" style="color: var(--brand-500); text-decoration: none;">Soporte</a>
          </p>
        </div>
      </div>
    `;
    
    this.attachEvents();
    Analytics.pageView('settings');
  }
  
  async loadSettings() {
    this.user = Store.getState('user');
    
    // Load settings from localStorage
    const saved = localStorage.getItem('app_settings');
    if (saved) {
      this.settings = { ...this.settings, ...JSON.parse(saved) };
    }
    
    // Apply dark mode if enabled
    if (this.settings.dark_mode) {
      document.documentElement.classList.add('dark');
    }
  }
  
  attachEvents() {
    // Dark mode toggle
    document.getElementById('dark-mode').addEventListener('change', (e) => {
      this.settings.dark_mode = e.target.checked;
      this.saveSettings();
      
      if (e.target.checked) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      
      Analytics.track('settings_changed', { setting: 'dark_mode', value: e.target.checked });
    });
    
    // Push notifications toggle
    document.getElementById('push-notifications').addEventListener('change', async (e) => {
      this.settings.notifications = e.target.checked;
      this.saveSettings();
      
      if (e.target.checked) {
        // Request permission
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
          e.target.checked = false;
          this.settings.notifications = false;
          alert('Permisos de notificación denegados');
        }
      }
      
      Analytics.track('settings_changed', { setting: 'notifications', value: e.target.checked });
    });
    
    // Auto sync toggle
    document.getElementById('auto-sync').addEventListener('change', (e) => {
      this.settings.auto_sync = e.target.checked;
      this.saveSettings();
      Analytics.track('settings_changed', { setting: 'auto_sync', value: e.target.checked });
    });
    
    // GPS accuracy
    document.getElementById('gps-accuracy').addEventListener('change', (e) => {
      this.settings.gps_accuracy = e.target.value;
      this.saveSettings();
      Analytics.track('settings_changed', { setting: 'gps_accuracy', value: e.target.value });
    });
  }
  
  saveSettings() {
    localStorage.setItem('app_settings', JSON.stringify(this.settings));
  }
  
  destroy() {
    // Cleanup
  }
}

// CSS for toggle switch
const style = document.createElement('style');
style.textContent = `
  .setting-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
  }
  
  .switch {
    position: relative;
    display: inline-block;
    width: 48px;
    height: 28px;
  }
  
  .switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  
  .slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: var(--gray-300);
    transition: .3s;
    border-radius: 28px;
  }
  
  .slider:before {
    position: absolute;
    content: "";
    height: 20px;
    width: 20px;
    left: 4px;
    bottom: 4px;
    background-color: white;
    transition: .3s;
    border-radius: 50%;
  }
  
  input:checked + .slider {
    background-color: var(--brand-500);
  }
  
  input:checked + .slider:before {
    transform: translateX(20px);
  }
`;
document.head.appendChild(style);
