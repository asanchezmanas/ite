// js/pages/battles.js
import Store from '../core/store.js';
import API from '../core/api.js';
import Analytics, { Events } from '../core/analytics.js';

export default class BattlesPage {
  constructor() {
    this.battles = [];
    this.activeTab = 'all'; // all, mine, critical
    this.autoRefreshInterval = null;
  }
  
  async render(container) {
    const startTime = Date.now();
    
    await this.loadBattles();
    
    container.innerHTML = `
      <div class="battles-page">
        <!-- Top Bar -->
        <div class="top-bar">
          <button class="btn-back" onclick="window.history.back()">←</button>
          <h1>Batallas Activas</h1>
          <button class="btn-icon" id="btn-refresh">🔄</button>
        </div>
        
        <!-- Stats Summary -->
        <div class="card" style="margin: 16px;">
          <div style="display: flex; justify-content: space-around; text-align: center;">
            <div>
              <div class="stat-value" style="font-size: 24px; color: var(--brand-500);">${this.battles.length}</div>
              <div class="stat-label">Global</div>
            </div>
            <div style="width: 1px; background: var(--border-color);"></div>
            <div>
              <div class="stat-value" style="font-size: 24px; color: var(--brand-500);">${this.getMyBattles().length}</div>
              <div class="stat-label">Tuyas</div>
            </div>
            <div style="width: 1px; background: var(--border-color);"></div>
            <div>
              <div class="stat-value" style="font-size: 24px; color: var(--error-500);">${this.getCriticalBattles().length}</div>
              <div class="stat-label">Críticas</div>
            </div>
          </div>
        </div>
        
        <!-- Tabs -->
        <div style="padding: 0 16px; margin-bottom: 16px;">
          <div style="display: flex; gap: 8px; background: var(--bg-secondary); padding: 4px; border-radius: var(--radius-lg);">
            <button class="tab-btn ${this.activeTab === 'all' ? 'active' : ''}" data-tab="all">
              Todas
            </button>
            <button class="tab-btn ${this.activeTab === 'mine' ? 'active' : ''}" data-tab="mine">
              Mis Batallas
            </button>
            <button class="tab-btn ${this.activeTab === 'critical' ? 'active' : ''}" data-tab="critical">
              Críticas
            </button>
          </div>
        </div>
        
        <!-- Battles List -->
        <div id="battles-list" style="padding: 0 16px 16px;">
          ${this.renderBattles()}
        </div>
        
        <!-- Auto refresh indicator -->
        <div style="position: fixed; bottom: 88px; right: 16px; background: var(--bg-secondary); padding: 8px 12px; border-radius: var(--radius-full); font-size: 12px; box-shadow: var(--shadow-sm);">
          <span id="refresh-indicator">🔄 Auto-actualización: 30s</span>
        </div>
      </div>
    `;
    
    this.attachEvents();
    this.startAutoRefresh();
    
    Analytics.trackPageTiming('battles', startTime);
    Analytics.pageView('battles');
  }
  
  async loadBattles() {
    try {
      const data = await API.risk.getBattles();
      this.battles = data.active || [];
    } catch (error) {
      console.error('Error loading battles:', error);
      Analytics.trackError(error, { page: 'battles' });
    }
  }
  
  getMyBattles() {
    const userId = Store.getState('user.id');
    return this.battles.filter(b => 
      b.attacker_id === userId || 
      b.defender_id === userId ||
      b.user_participation > 0
    );
  }
  
  getCriticalBattles() {
    return this.battles.filter(b => 
      b.is_critical || 
      b.conquest_progress > 80 ||
      b.time_remaining_hours < 12
    );
  }
  
  renderBattles() {
    let battles = this.battles;
    
    if (this.activeTab === 'mine') {
      battles = this.getMyBattles();
    } else if (this.activeTab === 'critical') {
      battles = this.getCriticalBattles();
    }
    
    if (battles.length === 0) {
      return `
        <div class="card" style="text-align: center; padding: 48px 24px;">
          <div style="font-size: 48px; margin-bottom: 16px;">⚔️</div>
          <h3 style="margin-bottom: 8px;">No hay batallas</h3>
          <p class="text-secondary">
            ${this.activeTab === 'mine' 
              ? 'Aún no estás participando en ninguna batalla' 
              : 'No hay batallas activas en este momento'}
          </p>
        </div>
      `;
    }
    
    return battles.map(battle => `
      <div class="card battle-card" style="margin-bottom: 12px; cursor: pointer;" data-battle-id="${battle.id}">
        <!-- Header -->
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
          <div>
            <h4 style="margin-bottom: 4px;">${battle.territory_name}</h4>
            <p class="text-xs text-secondary">
              ${battle.territory_type} • Hace ${this.formatTimeAgo(battle.started_at)}
            </p>
          </div>
          <div style="display: flex; gap: 4px;">
            ${battle.is_critical ? '<span class="badge badge-error">🔴 CRÍTICO</span>' : ''}
            ${battle.user_participation > 0 ? '<span class="badge badge-brand">Tu participación</span>' : ''}
          </div>
        </div>
        
        <!-- Combatants -->
        <div style="display: grid; grid-template-columns: 1fr auto 1fr; gap: 12px; margin-bottom: 12px;">
          <!-- Defender -->
          <div>
            <div style="font-size: 20px; margin-bottom: 4px;">${battle.defender_flag}</div>
            <div style="font-weight: 600;">${battle.defender_name}</div>
            <div class="text-sm text-secondary">${battle.defender_units} unidades</div>
          </div>
          
          <!-- VS -->
          <div style="display: flex; align-items: center; color: var(--text-secondary); font-weight: 600;">
            VS
          </div>
          
          <!-- Attacker -->
          <div style="text-align: right;">
            <div style="font-size: 20px; margin-bottom: 4px;">${battle.attacker_flag}</div>
            <div style="font-weight: 600;">${battle.attacker_name}</div>
            <div class="text-sm text-secondary">${battle.attacker_units} unidades</div>
          </div>
        </div>
        
        <!-- Progress Bar -->
        <div style="margin-bottom: 8px;">
          <div style="background: var(--gray-100); border-radius: var(--radius-md); height: 8px; overflow: hidden; position: relative;">
            <div style="background: var(--error-500); height: 100%; width: ${battle.conquest_progress}%; transition: width 0.3s;"></div>
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 10px; font-weight: 600; color: var(--gray-600);">
              ${battle.conquest_progress}%
            </div>
          </div>
        </div>
        
        <!-- Status -->
        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
          <span class="text-sm text-secondary">
            ${battle.conquest_progress >= 70 
              ? `🔴 Falta ${70 - battle.conquest_progress}% para conquista` 
              : `Progreso atacante: ${battle.conquest_progress}%`}
          </span>
          <span class="text-sm text-secondary">
            ⏱️ ${this.formatTimeRemaining(battle.time_remaining_hours)}
          </span>
        </div>
        
        <!-- User Contribution -->
        ${battle.user_participation > 0 ? `
          <div style="background: var(--brand-50); padding: 8px; border-radius: var(--radius-md); margin-bottom: 12px; font-size: 12px;">
            💪 Tu aporte: ${battle.user_participation} unidades
          </div>
        ` : ''}
        
        <!-- Actions -->
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-secondary btn-sm" style="flex: 1;" onclick="event.stopPropagation(); alert('Reforzar')">
            ⚔️ Reforzar
          </button>
          <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); alert('Compartir')">
            📢
          </button>
        </div>
      </div>
    `).join('');
  }
  
  attachEvents() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.activeTab = btn.dataset.tab;
        
        // Update UI
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        document.getElementById('battles-list').innerHTML = this.renderBattles();
        this.reattachBattleCardEvents();
        
        Analytics.track('battles_tab_changed', { tab: this.activeTab });
      });
    });
    
    // Refresh button
    document.getElementById('btn-refresh').addEventListener('click', async () => {
      await this.refresh();
    });
    
    // Battle cards
    this.reattachBattleCardEvents();
  }
  
  reattachBattleCardEvents() {
    document.querySelectorAll('.battle-card').forEach(card => {
      card.addEventListener('click', () => {
        const battleId = card.dataset.battleId;
        Analytics.track(Events.BATTLE_VIEWED, { battle_id: battleId });
        window.location.href = `/battle/${battleId}`;
      });
    });
  }
  
  async refresh() {
    const btn = document.getElementById('btn-refresh');
    btn.style.animation = 'spin 0.5s linear';
    
    await this.loadBattles();
    document.getElementById('battles-list').innerHTML = this.renderBattles();
    this.reattachBattleCardEvents();
    
    setTimeout(() => {
      btn.style.animation = '';
    }, 500);
  }
  
  startAutoRefresh() {
    let countdown = 30;
    
    this.autoRefreshInterval = setInterval(async () => {
      countdown--;
      
      const indicator = document.getElementById('refresh-indicator');
      if (indicator) {
        indicator.textContent = `🔄 Auto-actualización: ${countdown}s`;
      }
      
      if (countdown <= 0) {
        await this.refresh();
        countdown = 30;
      }
    }, 1000);
  }
  
  formatTimeAgo(timestamp) {
    const seconds = Math.floor((Date.now() - new Date(timestamp)) / 1000);
    
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
    return `${Math.floor(seconds / 86400)}d`;
  }
  
  formatTimeRemaining(hours) {
    if (hours < 1) return `${Math.floor(hours * 60)}m restantes`;
    if (hours < 24) return `${Math.floor(hours)}h restantes`;
    return `${Math.floor(hours / 24)}d restantes`;
  }
  
  destroy() {
    if (this.autoRefreshInterval) {
      clearInterval(this.autoRefreshInterval);
    }
  }
}

// CSS for tab buttons
const style = document.createElement('style');
style.textContent = `
  .tab-btn {
    flex: 1;
    padding: 8px 16px;
    background: transparent;
    border: none;
    border-radius: var(--radius-md);
    font-size: 14px;
    font-weight: 500;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s;
    font-family: var(--font-family);
  }
  
  .tab-btn.active {
    background: var(--bg-primary);
    color: var(--text-primary);
    box-shadow: var(--shadow-xs);
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;
document.head.appendChild(style);
