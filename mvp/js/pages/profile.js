// js/pages/profile.js
import Store from '../core/store.js';
import API from '../core/api.js';
import Auth from '../core/auth.js';
import Analytics from '../core/analytics.js';

export default class ProfilePage {
  constructor() {
    this.user = null;
    this.stats = null;
    this.achievements = [];
    this.recentActivities = [];
  }
  
  async render(container) {
    const startTime = Date.now();
    
    await this.loadProfile();
    
    container.innerHTML = `
      <div class="profile-page">
        <!-- Top Bar -->
        <div class="top-bar">
          <button class="btn-back" onclick="window.history.back()">←</button>
          <h1>Perfil</h1>
          <button class="btn-icon" id="btn-settings">⚙️</button>
        </div>
        
        <!-- Profile Header -->
        <div class="card" style="margin: 16px; text-align: center;">
          <!-- Avatar -->
          <div style="width: 80px; height: 80px; margin: 0 auto 16px; border-radius: 50%; background: linear-gradient(135deg, var(--brand-500), var(--brand-600)); display: flex; align-items: center; justify-content: center; color: white; font-size: 32px; font-weight: 700;">
            ${this.getInitials(this.user?.username)}
          </div>
          
          <!-- Username -->
          <h2 style="margin-bottom: 4px;">@${this.user?.username}</h2>
          <p class="text-secondary">${this.user?.full_name || this.user?.email}</p>
          
          <!-- Membership -->
          <p class="text-xs text-secondary" style="margin-top: 8px;">
            Miembro desde ${this.formatDate(this.user?.created_at)}
          </p>
          
          <!-- Edit Button -->
          <button class="btn btn-secondary btn-sm" style="margin-top: 16px;" id="btn-edit-profile">
            ✏️ Editar Perfil
          </button>
        </div>
        
        <!-- Main Stats -->
        <div class="card" style="margin: 0 16px 16px;">
          <h3 style="margin-bottom: 16px;">📊 Estadísticas</h3>
          <div class="stats-grid" style="grid-template-columns: repeat(3, 1fr);">
            <div class="stat-card">
              <div class="stat-value">${this.stats?.total_km || 0}</div>
              <div class="stat-label">km total</div>
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
        
        <!-- Rankings -->
        <div class="card" style="margin: 0 16px 16px;">
          <h3 style="margin-bottom: 12px;">🏆 Rankings</h3>
          <div style="display: flex; flex-direction: column; gap: 8px;">
            ${this.renderRankings()}
          </div>
        </div>
        
        <!-- Conquest Stats -->
        <div class="card" style="margin: 0 16px 16px;">
          <h3 style="margin-bottom: 12px;">⚔️ Conquista</h3>
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span class="text-secondary">Territorios controlados</span>
            <strong>${this.stats?.territories_controlled || 0}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span class="text-secondary">Batallas participadas</span>
            <strong>${this.stats?.battles_participated || 0}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span class="text-secondary">Conquistas logradas</span>
            <strong>${this.stats?.conquests_achieved || 0}</strong>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span class="text-secondary">Territorios defendidos</span>
            <strong>${this.stats?.territories_defended || 0}</strong>
          </div>
        </div>
        
        <!-- Activity Stats -->
        <div class="card" style="margin: 0 16px 16px;">
          <h3 style="margin-bottom: 12px;">🏃 Actividades</h3>
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span class="text-secondary">Total actividades</span>
            <strong>${this.stats?.total_activities || 0}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span class="text-secondary">Promedio semanal</span>
            <strong>${this.stats?.weekly_average || 0}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span class="text-secondary">Racha actual</span>
            <strong>${this.stats?.current_streak || 0} días ${this.stats?.current_streak >= 3 ? '🔥' : ''}</strong>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span class="text-secondary">Mejor racha</span>
            <strong>${this.stats?.best_streak || 0} días</strong>
          </div>
        </div>
        
        <!-- Achievements -->
        <div style="margin: 0 16px 16px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h3>🏅 Logros (${this.achievements.filter(a => a.unlocked).length}/${this.achievements.length})</h3>
            <a href="/achievements" style="color: var(--brand-500); text-decoration: none; font-size: 14px;">Ver todos</a>
          </div>
          <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px;">
            ${this.renderAchievements()}
          </div>
        </div>
        
        <!-- Team -->
        ${this.user?.team_id ? `
          <div class="card" style="margin: 0 16px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div>
                <h4 style="margin-bottom: 4px;">👥 ${this.user.team_name}</h4>
                <p class="text-sm text-secondary">
                  ${this.user.team_members} miembros • Rank #${this.user.team_rank}
                </p>
              </div>
              <button class="btn btn-secondary btn-sm" onclick="window.location.href='/team'">
                Ver
              </button>
            </div>
          </div>
        ` : `
          <div class="card" style="margin: 0 16px 16px; text-align: center; padding: 32px 24px;">
            <div style="font-size: 48px; margin-bottom: 12px;">👥</div>
            <h4 style="margin-bottom: 8px;">Únete a un equipo</h4>
            <p class="text-sm text-secondary" style="margin-bottom: 16px;">
              Conquista territorios junto a otros corredores
            </p>
            <button class="btn btn-primary" onclick="alert('Crear/Unirse a equipo')">
              Buscar Equipos
            </button>
          </div>
        `}
        
        <!-- Recent Activities -->
        <div style="margin: 0 16px 16px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h3>📅 Actividades Recientes</h3>
            <a href="/activities" style="color: var(--brand-500); text-decoration: none; font-size: 14px;">Ver todas</a>
          </div>
          ${this.renderRecentActivities()}
        </div>
        
        <!-- Actions -->
        <div style="padding: 16px; display: flex; flex-direction: column; gap: 12px;">
          <button class="btn btn-secondary w-full" id="btn-settings-full">
            ⚙️ Configuración
          </button>
          <button class="btn btn-secondary w-full" id="btn-logout" style="color: var(--error-500);">
            🚪 Cerrar Sesión
          </button>
        </div>
      </div>
    `;
    
    this.attachEvents();
    
    Analytics.trackPageTiming('profile', startTime);
    Analytics.pageView('profile');
  }
  
  async loadProfile() {
    try {
      this.user = Store.getState('user') || await API.user.getProfile();
      this.stats = await API.user.getStats();
      
      // Mock achievements
      this.achievements = [
        { id: 1, icon: '🏅', name: '5K', unlocked: true },
        { id: 2, icon: '⭐', name: '10K', unlocked: true },
        { id: 3, icon: '🏆', name: 'Maratón', unlocked: false },
        { id: 4, icon: '🎯', name: 'Conquistador', unlocked: true },
        { id: 5, icon: '🔒', name: '???', unlocked: false },
        { id: 6, icon: '🔒', name: '???', unlocked: false },
        { id: 7, icon: '🔒', name: '???', unlocked: false },
        { id: 8, icon: '🔒', name: '???', unlocked: false }
      ];
      
      // Load recent activities
      const activitiesData = await API.activities.list();
      this.recentActivities = (activitiesData.activities || []).slice(0, 5);
      
    } catch (error) {
      console.error('Error loading profile:', error);
      Analytics.trackError(error, { page: 'profile' });
    }
  }
  
  renderRankings() {
    const rankings = [
      { name: 'Mundial', rank: this.stats?.global_rank || '---', total: '500,000', flag: '🌍' },
      { name: 'España', rank: this.stats?.spain_rank || '---', total: '15,000', flag: '🇪🇸' },
      { name: 'Cataluña', rank: this.stats?.catalonia_rank || '---', total: '5,000', flag: '🏴' },
      { name: 'Barcelona', rank: this.stats?.barcelona_rank || '---', total: '3,000', flag: '📍' }
    ];
    
    return rankings.map(r => `
      <div style="display: flex; justify-content: space-between; padding: 12px; background: var(--bg-secondary); border-radius: var(--radius-md);">
        <div style="display: flex; align-items: center; gap: 12px;">
          <span style="font-size: 24px;">${r.flag}</span>
          <span style="font-weight: 500;">${r.name}</span>
        </div>
        <div style="text-align: right;">
          <div style="font-weight: 600; color: var(--brand-500);">#${r.rank}</div>
          <div class="text-xs text-secondary">de ${r.total}</div>
        </div>
      </div>
    `).join('');
  }
  
  renderAchievements() {
    return this.achievements.map(a => `
      <div style="
        aspect-ratio: 1;
        background: ${a.unlocked ? 'var(--brand-50)' : 'var(--gray-100)'};
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        ${!a.unlocked ? 'filter: grayscale(1); opacity: 0.5;' : ''}
        cursor: pointer;
      " title="${a.name}">
        ${a.icon}
      </div>
    `).join('');
  }
  
  renderRecentActivities() {
    if (this.recentActivities.length === 0) {
      return `
        <div class="card" style="text-align: center; padding: 32px 24px;">
          <div style="font-size: 48px; margin-bottom: 12px;">🏃</div>
          <p class="text-secondary">Aún no hay actividades</p>
        </div>
      `;
    }
    
    return this.recentActivities.map(activity => `
      <div class="card" style="margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <div style="font-weight: 600; margin-bottom: 4px;">
              ${activity.distance_km} km • ${this.formatDuration(activity.duration_minutes)}
            </div>
            <p class="text-xs text-secondary">
              ${this.formatActivityType(activity.activity_type)} • ${this.formatDate(activity.recorded_at)}
            </p>
          </div>
          <div class="badge badge-brand">
            +${activity.points_earned || Math.floor(activity.distance_km * 10)} pts
          </div>
        </div>
      </div>
    `).join('');
  }
  
  attachEvents() {
    // Settings button
    document.getElementById('btn-settings').addEventListener('click', () => {
      window.location.href = '/settings';
    });
    
    document.getElementById('btn-settings-full').addEventListener('click', () => {
      window.location.href = '/settings';
    });
    
    // Edit profile
    document.getElementById('btn-edit-profile').addEventListener('click', () => {
      alert('Editar perfil en desarrollo');
    });
    
    // Logout
    document.getElementById('btn-logout').addEventListener('click', async () => {
      if (confirm('¿Seguro que quieres cerrar sesión?')) {
        Analytics.track('logout');
        await Auth.logout();
      }
    });
  }
  
  getInitials(username) {
    if (!username) return '?';
    return username.substring(0, 2).toUpperCase();
  }
  
  formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', { 
      month: 'short', 
      year: 'numeric' 
    });
  }
  
  formatDuration(minutes) {
    const mins = Math.floor(minutes);
    const secs = Math.floor((minutes - mins) * 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
  
  formatActivityType(type) {
    const types = {
      run: '🏃 Correr',
      walk: '🚶 Caminar',
      bike: '🚴 Bicicleta',
      gym: '💪 Gym'
    };
    return types[type] || type;
  }
  
  destroy() {
    // Cleanup
  }
}
