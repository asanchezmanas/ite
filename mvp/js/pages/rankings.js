// js/pages/rankings.js

import API from '../core/api.js';
import Analytics from '../core/analytics.js';

export default class RankingsPage {
  constructor() {
    this.rankings = [];
    this.activeTab = 'users'; // users, teams, zones
    this.metric = 'points'; // points, km, zones
    this.userPosition = null;
  }
  
  async render(container) {
    await this.loadRankings();
    
    container.innerHTML = `
      <div class="rankings-page">
        <!-- Top Bar -->
        <div class="top-bar">
          <button class="btn-back" onclick="window.history.back()">←</button>
          <h1>Rankings</h1>
          <button class="btn-icon" id="btn-filter">🔄</button>
        </div>
        
        <!-- Tabs -->
        <div style="padding: 16px 16px 0;">
          <div style="display: flex; gap: 8px; background: var(--bg-secondary); padding: 4px; border-radius: var(--radius-lg);">
            <button class="tab-btn ${this.activeTab === 'users' ? 'active' : ''}" data-tab="users">
              👥 Usuarios
            </button>
            <button class="tab-btn ${this.activeTab === 'teams' ? 'active' : ''}" data-tab="teams">
              🏆 Equipos
            </button>
            <button class="tab-btn ${this.activeTab === 'zones' ? 'active' : ''}" data-tab="zones">
              🗺️ Zonas
            </button>
          </div>
        </div>
        
        <!-- Metric selector -->
        <div style="padding: 16px;">
          <div style="display: flex; gap: 8px;">
            <button class="metric-btn ${this.metric === 'points' ? 'active' : ''}" data-metric="points">
              📊 Puntos
            </button>
            <button class="metric-btn ${this.metric === 'km' ? 'active' : ''}" data-metric="km">
              📏 KM
            </button>
            <button class="metric-btn ${this.metric === 'zones' ? 'active' : ''}" data-metric="zones">
              ⚔️ Zonas
            </button>
          </div>
        </div>
        
        <!-- User Position -->
        ${this.userPosition ? `
          <div class="card" style="margin: 0 16px 16px; border: 2px solid var(--brand-500);">
            <div style="text-align: center; margin-bottom: 12px;">
              <div class="text-sm text-secondary">Tu Posición</div>
              <div style="font-size: 32px; font-weight: 700; color: var(--brand-500);">
                #${this.userPosition.rank}
              </div>
              <div class="text-sm text-secondary">
                de ${this.userPosition.total.toLocaleString()} en España
              </div>
            </div>
            <div style="display: flex; justify-content: space-around; padding-top: 12px; border-top: 1px solid var(--border-color);">
              <div style="text-align: center;">
                <div class="font-bold">${this.userPosition.points}</div>
                <div class="text-xs text-secondary">puntos</div>
              </div>
              <div style="text-align: center;">
                <div class="font-bold">${this.userPosition.km}</div>
                <div class="text-xs text-secondary">km</div>
              </div>
              <div style="text-align: center;">
                <div class="font-bold">${this.userPosition.zones}</div>
                <div class="text-xs text-secondary">zonas</div>
              </div>
            </div>
            ${this.userPosition.rank_change !== 0 ? `
              <div style="text-align: center; margin-top: 12px; color: ${this.userPosition.rank_change > 0 ? 'var(--success-500)' : 'var(--error-500)'}; font-size: 14px;">
                ${this.userPosition.rank_change > 0 ? '↑' : '↓'} ${Math.abs(this.userPosition.rank_change)} posiciones esta semana
              </div>
            ` : ''}
          </div>
        ` : ''}
        
        <!-- Rankings List -->
        <div style="padding: 0 16px;">
          <h3 style="margin-bottom: 12px;">Top 100</h3>
          <div id="rankings-list">
            ${this.renderRankings()}
          </div>
        </div>
      </div>
    `;
    
    this.attachEvents();
    Analytics.pageView('rankings');
  }
  
  async loadRankings() {
    try {
      const data = await API.leaderboard[this.activeTab](this.metric);
      this.rankings = data.rankings || [];
      this.userPosition = data.user_position || null;
    } catch (error) {
      console.error('Error loading rankings:', error);
    }
  }
  
  renderRankings() {
    if (this.rankings.length === 0) {
      return `
        <div class="card" style="text-align: center; padding: 48px 24px;">
          <div style="font-size: 48px; margin-bottom: 16px;">🏆</div>
          <p class="text-secondary">No hay rankings disponibles</p>
        </div>
      `;
    }
    
    return this.rankings.map((item, index) => `
      <div class="card ranking-card" style="margin-bottom: 8px; ${item.is_user ? 'border: 2px solid var(--brand-500);' : ''}">
        <div style="display: flex; align-items: center; gap: 16px;">
          <!-- Rank -->
          <div style="font-size: 20px; font-weight: 700; min-width: 40px; text-align: center; color: ${
            item.rank <= 3 ? 'var(--warning-500)' : 'var(--text-secondary)'
          };">
            ${item.rank <= 3 ? ['🥇', '🥈', '🥉'][item.rank - 1] : '#' + item.rank}
          </div>
          
          <!-- Info -->
          <div style="flex: 1;">
            <div style="font-weight: 600; margin-bottom: 4px;">
              ${item.name}
              ${item.is_user ? '<span class="badge badge-brand" style="margin-left: 8px;">TÚ</span>' : ''}
            </div>
            <div class="text-sm text-secondary">
              ${this.metric === 'points' ? item.points + ' pts' : ''}
              ${this.metric === 'km' ? item.km + ' km' : ''}
              ${this.metric === 'zones' ? item.zones + ' zonas' : ''}
              ${item.flag ? ' • ' + item.flag : ''}
            </div>
          </div>
          
          <!-- Value -->
          <div style="text-align: right;">
            <div style="font-size: 18px; font-weight: 600; color: var(--brand-500);">
              ${this.metric === 'points' ? item.points : ''}
              ${this.metric === 'km' ? item.km : ''}
              ${this.metric === 'zones' ? item.zones : ''}
            </div>
            ${item.trend ? `
              <div class="text-xs" style="color: ${item.trend > 0 ? 'var(--success-500)' : 'var(--error-500)'};">
                ${item.trend > 0 ? '↑' : '↓'} ${Math.abs(item.trend)}
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    `).join('');
  }
  
  attachEvents() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        this.activeTab = btn.dataset.tab;
        await this.refresh();
        Analytics.track('rankings_tab_changed', { tab: this.activeTab });
      });
    });
    
    // Metric switching
    document.querySelectorAll('.metric-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        this.metric = btn.dataset.metric;
        await this.refresh();
        Analytics.track('rankings_metric_changed', { metric: this.metric });
      });
    });
    
    // Refresh button
    document.getElementById('btn-filter').addEventListener('click', async () => {
      await this.refresh();
    });
  }
  
  async refresh() {
    await this.loadRankings();
    
    // Update tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === this.activeTab);
    });
    
    // Update metrics
    document.querySelectorAll('.metric-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.metric === this.metric);
    });
    
    // Update list
    document.getElementById('rankings-list').innerHTML = this.renderRankings();
  }
  
  destroy() {
    // Cleanup
  }
}

// CSS for metric buttons
const style = document.createElement('style');
style.textContent = `
  .metric-btn {
    flex: 1;
    padding: 8px 12px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    font-size: 13px;
    font-weight: 500;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s;
    font-family: var(--font-family);
  }
  
  .metric-btn.active {
    background: var(--brand-500);
    color: white;
    border-color: var(--brand-500);
  }
`;
document.head.appendChild(style);
