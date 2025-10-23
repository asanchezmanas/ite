// js/pages/home.js
import Store from '../core/store.js';
import API from '../core/api.js';
import Router from '../core/router.js';

export default class HomePage {
  constructor() {
    this.user = null;
    this.stats = null;
    this.alerts = [];
    this.battles = [];
  }
  
  async render(container) {
    await this.loadData();
    
    container.innerHTML = `
      <div class="home-page">
        <!-- Top Bar -->
        <div class="top-bar">
          <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 40px; height: 40px; border-radius: 50%; background: var(--brand-500); display: flex; align-items: center; justify-content: center; color: white; font-weight: 600;">
              ${this.getInitials(this.user?.username)}
            </div>
            <div>
              <div style="font-weight: 600;">@${this.user?.username}</div>
              <div class="text-xs text-secondary">#${this.stats?.global_rank || '---'} 🇪🇸</div>
            </div>
          </div>
          <button class="btn-icon" id="btn-notifications">
            🔔
            ${this.alerts.length > 0 ? `<span class="badge badge-error" style="position: absolute; top: 4px; right: 4px; min-width: 18px; height: 18px; padding: 0 4px; font-size: 10px;">${this.alerts.length}</span>` : ''}
          </button>
        </div>
        
        <!-- User Stats Card -->
        <div class="card" style="margin: 16px;">
          <div class="stats-grid" style="grid-template-columns: repeat(3, 1fr);">
            <div class="stat-card">
              <div class="stat-value">${this.stats?.total_km || 0}</div>
              <div class="stat-label">km</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">${this.stats?.total_points || 0}</div>
              <div class="stat-label">puntos</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">${this.stats?.zones_controlled || 0}</div>
              <div class="stat-label">zonas</div>
            </div>
          </div>
        </div>
        
        <!-- Critical Alerts -->
        ${this.alerts.length > 0 ? `
          <div style="margin: 0 16px 16px;">
            <h3 style="margin-bottom: 12px;">⚠️ Alertas Críticas</h3>
            ${this.renderAlerts()}
          </div>
        ` : ''}
        
        <!-- Territory Status -->
        <div style="margin: 0 16px 16px;">
          <h3 style="margin-bottom: 12px;">📊 Tu Situación</h3>
          
          <!-- Spain -->
          <div class="card" style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
              <div>
                <h4 style="margin-bottom: 4px;">🇪🇸 España</h4>
                <p class="text-sm text-secondary">Territorios: ${this.stats?.spain_territories || 0} (#${this.stats?.spain_rank || '--'})</p>
              </div>
              ${this.stats?.spain_under_attack ? `
                <span class="badge badge-error">⚔️ ${this.stats.spain_attacks} ataques</span>
              ` : `
                <span class="badge badge-success">✓ Seguro</span>
              `}
            </div>
            
            ${this.stats?.spain_under_attack ? `
              <button class="btn btn-danger btn-sm w-full" style="margin-top: 12px;" onclick="window.location.href='/battles'">
                🚨 Ver Batallas
              </button>
            ` : ''}
          </div>
          
          <!-- Cataluña -->
          <div class="card" style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: between; align-items: start;">
              <div>
                <h4 style="margin-bottom: 4px;">🏴 Cataluña</h4>
                <p class="text-sm text-secondary">Unidades: ${this.stats?.catalonia_units || 0}</p>
              </div>
              ${this.stats?.catalonia_battle ? `
                <div style="margin-top: 8px;">
                  <div style="background: var(--gray-100); border-radius: var(--radius-md); height: 6px; overflow: hidden; margin-bottom: 4px;">
                    <div style="background: var(--error-500); height: 100%; width: ${this.stats.catalonia_battle_progress}%;"></div>
                  </div>
                  <p class="text-xs text-secondary" style="text-align: center;">
                    🇫🇷 Francia: ${this.stats.catalonia_battle_progress}% vs ${100 - this.stats.catalonia_battle_progress}%
                  </p>
                </div>
              ` : ''}
            </div>
          </div>
          
          <!-- Barcelona -->
          <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div>
                <h4 style="margin-bottom: 4px;">📍 Barcelona</h4>
                <p class="text-sm text-secondary">Tu ciudad base</p>
              </div>
              <button class="btn btn-secondary btn-sm" onclick="window.location.href='/map'">
                Ver Mapa
              </button>
            </div>
          </div>
        </div>
        
        <!-- Active Battles -->
        ${this.battles.length > 0 ? `
          <div style="margin: 0 16px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
              <h3>⚔️ Batallas Activas</h3>
              <a href="/battles" style="color: var(--brand-500); text-decoration: none; font-size: 14px;">Ver todas</a>
            </div>
            ${this.renderBattles()}
          </div>
        ` : ''}
        
        <!-- Recent Achievements -->
        ${this.stats?.recent_achievements?.length > 0 ? `
          <div style="margin: 0 16px 16px;">
            <h3 style="margin-bottom: 12px;">🏆 Logros Recientes</h3>
            <div style="display: flex; gap: 8px; overflow-x: auto; padding-bottom: 8px;">
              ${this.renderAchievements()}
            </div>
          </div>
        ` : ''}
        
        <!-- Quick Actions -->
        <div style="padding: 16px;">
          <h3 style="margin-bottom: 12px;">Acciones Rápidas</h3>
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
            <button class="btn btn-primary" style="flex-direction: column; padding: 16px; height: auto;" onclick="window.location.href='/tracking'">
              <span style="font-size: 24px;">🏃</span>
              <span style="font-size: 12px; margin-top: 4px;">Entrenar</span>
            </button>
            <button class="btn btn-secondary" style="flex-direction: column; padding: 16px; height: auto;" onclick="window.location.href='/map'">
              <span style="font-size: 24px;">🗺️</span>
              <span style="font-size: 12px; margin-top: 4px;">Mapa</span>
            </button>
            <button class="btn btn-secondary" style="flex-direction: column; padding: 16px; height: auto;" onclick="window.location.href='/team'">
              <span style="font-size: 24px;">👥</span>
              <span style="font-size: 12px; margin-top: 4px;">Equipo</span>
            </button>
          </div>
        </div>
      </div>
    `;
    
    this.attachEvents();
  }
  
  async loadData() {
    try {
      // Load user
      this.user = Store.getState('user') || await API.user.getProfile();
      Store.setState('user', this.user);
      
      // Load stats
      this.stats = await API.user.getStats();
      
      // Load critical alerts
      this.alerts = await this.loadAlerts();
      
      // Load active battles
      const battlesData = await API.risk.getBattles();
      this.battles = (battlesData.active || []).slice(0, 3); // Top 3
      
    } catch (error) {
      console.error('Error loading home data:', error);
    }
  }
  
  async loadAlerts() {
    // Mock critical alerts - replace with API call
    const alerts = [];
    
    if (this.stats?.spain_under_attack) {
      alerts.push({
        id: 'alert-1',
        type: 'critical',
        title: '🔴 Francia conquista Pirineos',
        message: 'Se necesitan 50 unidades YA',
        action: 'defend',
        actionText: 'DEFENDER AHORA',
        territoryId: 'territory-1'
      });
    }
    
    if (this.stats?.catalonia_battle) {
      alerts.push({
        id: 'alert-2',
        type: 'warning',
        title: '🟠 Cataluña bajo presión',
        message: 'Francia ganando últimas 24h',
        action: 'view_battle',
        actionText: 'VER BATALLA',
        battleId: 'battle-1'
      });
    }
    
    return alerts;
  }
  
  renderAlerts() {
    return this.alerts.map(alert => `
      <div class="card" style="margin-bottom: 12px; border-left: 4px solid ${alert.type === 'critical' ? 'var(--error-500)' : 'var(--warning-500)'};">
        <h4 style="margin-bottom: 4px;">${alert.title}</h4>
        <p class="text-sm text-secondary" style="margin-bottom: 12px;">${alert.message}</p>
        <button class="btn ${alert.type === 'critical' ? 'btn-danger' : 'btn-primary'} w-full" onclick="alert('Acción: ${alert.action}')">
          ${alert.actionText}
        </button>
      </div>
    `).join('');
  }
  
  renderBattles() {
    return this.battles.map(battle => `
      <div class="card" style="margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
          <h4>${battle.territory_name}</h4>
          <span class="badge badge-error">⚔️ EN VIVO</span>
        </div>
        
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px;">
          <span>${battle.defender_flag} ${battle.defender_name}</span>
          <span style="color: var(--text-secondary);">VS</span>
          <span>${battle.attacker_flag} ${battle.attacker_name}</span>
        </div>
        
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; font-weight: 600;">
          <span>${battle.defender_units}</span>
          <span style="color: var(--text-secondary);">unidades</span>
          <span>${battle.attacker_units}</span>
        </div>
        
        <div style="background: var(--gray-100); border-radius: var(--radius-md); height: 6px; overflow: hidden; margin-bottom: 8px;">
          <div style="background: var(--error-500); height: 100%; width: ${battle.conquest_progress}%;"></div>
        </div>
        
        <p class="text-xs text-secondary" style="text-align: center; margin-bottom: 12px;">
          ${battle.conquest_progress}% hacia conquista
        </p>
        
        <button class="btn btn-secondary btn-sm w-full" onclick="window.location.href='/battle/${battle.id}'">
          👁️ Ver Detalle
        </button>
      </div>
    `).join('');
  }
  
  renderAchievements() {
    return this.stats.recent_achievements.map(achievement => `
      <div class="card" style="min-width: 120px; text-align: center; padding: 16px;">
        <div style="font-size: 32px; margin-bottom: 8px;">${achievement.icon}</div>
        <p class="text-xs font-bold">${achievement.name}</p>
        <p class="text-xs text-secondary">${achievement.date}</p>
      </div>
    `).join('');
  }
  
  getInitials(username) {
    if (!username) return '?';
    return username.substring(0, 2).toUpperCase();
  }
  
  attachEvents() {
    document.getElementById('btn-notifications')?.addEventListener('click', () => {
      // Show notifications modal
      alert('Notificaciones: ' + this.alerts.length);
    });
  }
  
  destroy() {
    // Cleanup
  }
}
