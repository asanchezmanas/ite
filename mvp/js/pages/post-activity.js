// js/pages/post-activity.js
import Store from '../core/store.js';
import API from '../core/api.js';

export default class PostActivityPage {
  constructor() {
    this.activityId = window.location.pathname.split('/')[2];
    this.activity = null;
    this.suggestions = [];
    this.allocations = [];
    this.totalUnits = 0;
    this.remainingUnits = 0;
  }
  
  async render(container) {
    // Load activity data
    await this.loadActivity();
    
    container.innerHTML = `
      <div class="post-activity-page">
        <!-- Top Bar -->
        <div class="top-bar">
          <button class="btn-back" onclick="window.history.back()">←</button>
          <h1>¡Actividad Completada!</h1>
        </div>
        
        <!-- Activity Summary -->
        <div class="card" style="margin: 16px;">
          <div style="text-align: center; margin-bottom: 24px;">
            <div style="font-size: 48px; margin-bottom: 8px;">🎉</div>
            <h2 style="margin-bottom: 8px;">${this.activity.distance_km} km</h2>
            <p class="text-secondary">¡Excelente entrenamiento!</p>
          </div>
          
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">${this.formatDuration(this.activity.duration_minutes)}</div>
              <div class="stat-label">Tiempo</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">${this.calculatePace(this.activity)}</div>
              <div class="stat-label">Pace</div>
            </div>
          </div>
        </div>
        
        <!-- Auto Defense -->
        <div class="card" style="margin: 16px; border-left: 4px solid var(--success-500);">
          <h3 style="margin-bottom: 12px;">✅ Defensa Automática Aplicada</h3>
          <div style="background: var(--success-50); padding: 12px; border-radius: var(--radius-md);">
            <div style="margin-bottom: 8px;">🇪🇸 España: +${this.totalUnits} unidades</div>
            <div style="margin-bottom: 8px;">🏴 Cataluña: +${this.totalUnits} unidades</div>
            <div>📍 Barcelona: +${this.totalUnits} unidades</div>
          </div>
        </div>
        
        <!-- Attack Distribution -->
        <div class="card" style="margin: 16px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3>🎯 ¿Dónde Atacar?</h3>
            <div class="badge badge-brand">${this.remainingUnits} restantes</div>
          </div>
          
          <p class="text-secondary text-sm" style="margin-bottom: 16px;">
            Distribuye tus ${this.totalUnits} unidades estratégicamente
          </p>
          
          <!-- Suggestions -->
          <div id="suggestions-list">
            ${this.renderSuggestions()}
          </div>
          
          <!-- Manual button -->
          <button class="btn btn-secondary w-full" style="margin-top: 16px;" onclick="alert('Abrir mapa en desarrollo')">
            🗺️ Seleccionar en Mapa
          </button>
        </div>
        
        <!-- Actions -->
        <div style="padding: 16px; display: flex; gap: 12px;">
          <button class="btn btn-secondary" id="btn-skip">
            🛡️ Solo Defender
          </button>
          <button class="btn btn-primary" id="btn-confirm" style="flex: 1;">
            ✅ Confirmar Ataques
          </button>
        </div>
      </div>
    `;
    
    this.attachEvents();
  }
  
  async loadActivity() {
    try {
      // Mock data for now - replace with real API call
      this.activity = {
        distance_km: 10.5,
        duration_minutes: 52,
        activity_type: 'run'
      };
      
      // Calculate units (10 km = 10 units for simplicity)
      this.totalUnits = Math.floor(this.activity.distance_km);
      this.remainingUnits = this.totalUnits;
      
      // Load strategic suggestions from backend
      this.suggestions = [
        {
          id: 'territory-1',
          name: 'Frontera Pirineos',
          priority: 'high',
          reason: 'Francia ganando (+8% hoy)',
          recommended_units: 8,
          success_probability: 65
        },
        {
          id: 'territory-2',
          name: 'Madrid',
          priority: 'medium',
          reason: 'Rivalidad histórica',
          recommended_units: 3,
          success_probability: 35
        }
      ];
      
      // Initialize allocations
      this.allocations = this.suggestions.map(s => ({
        territoryId: s.id,
        territoryName: s.name,
        units: 0
      }));
      
    } catch (error) {
      console.error('Error loading activity:', error);
    }
  }
  
  renderSuggestions() {
    return this.suggestions.map((suggestion, index) => `
      <div class="card" style="margin-bottom: 12px; ${suggestion.priority === 'high' ? 'border-left: 4px solid var(--error-500);' : 'border-left: 4px solid var(--warning-500);'}">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
          <div>
            <h4 style="margin-bottom: 4px;">${suggestion.name}</h4>
            <p class="text-xs text-secondary">${suggestion.reason}</p>
          </div>
          <span class="badge ${suggestion.priority === 'high' ? 'badge-error' : 'badge-brand'}">
            ${suggestion.priority === 'high' ? '🔴 CRÍTICO' : '🟡 MEDIO'}
          </span>
        </div>
        
        <div class="slider-container">
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span class="text-sm text-secondary">Unidades</span>
            <span class="font-bold" id="units-${index}">0</span>
          </div>
          <input 
            type="range" 
            class="slider" 
            id="slider-${index}"
            min="0" 
            max="${this.totalUnits}" 
            value="0"
            data-index="${index}"
          >
          <div style="display: flex; justify-content: space-between; margin-top: 8px; font-size: 12px;">
            <span class="text-secondary">Éxito: ${suggestion.success_probability}%</span>
            <span class="text-secondary">Recomendado: ${suggestion.recommended_units}</span>
          </div>
        </div>
        
        <button class="btn btn-primary btn-sm w-full" style="margin-top: 12px;" onclick="this.previousElementSibling.querySelector('input').value=${suggestion.recommended_units}; this.previousElementSibling.querySelector('input').dispatchEvent(new Event('input'))">
          ⚡ Aplicar Recomendado
        </button>
      </div>
    `).join('');
  }
  
  attachEvents() {
    // Slider events
    document.querySelectorAll('.slider').forEach(slider => {
      slider.addEventListener('input', (e) => {
        const index = parseInt(e.target.dataset.index);
        const value = parseInt(e.target.value);
        
        // Update display
        document.getElementById(`units-${index}`).textContent = value;
        
        // Update allocation
        this.allocations[index].units = value;
        
        // Recalculate remaining
        this.updateRemaining();
      });
    });
    
    // Skip button
    document.getElementById('btn-skip').addEventListener('click', () => {
      this.confirmActivity(true);
    });
    
    // Confirm button
    document.getElementById('btn-confirm').addEventListener('click', () => {
      this.confirmActivity(false);
    });
  }
  
  updateRemaining() {
    const used = this.allocations.reduce((sum, a) => sum + a.units, 0);
    this.remainingUnits = this.totalUnits - used;
    
    // Update badge
    const badge = document.querySelector('.badge-brand');
    if (badge) {
      badge.textContent = `${this.remainingUnits} restantes`;
      
      if (this.remainingUnits < 0) {
        badge.className = 'badge badge-error';
        badge.textContent = `¡${Math.abs(this.remainingUnits)} de más!`;
      } else {
        badge.className = 'badge badge-brand';
      }
    }
    
    // Disable/enable confirm
    const btnConfirm = document.getElementById('btn-confirm');
    btnConfirm.disabled = this.remainingUnits < 0;
  }
  
  async confirmActivity(skipAttacks = false) {
    try {
      const btnConfirm = document.getElementById('btn-confirm');
      btnConfirm.disabled = true;
      btnConfirm.innerHTML = '<span class="loading"></span> Guardando...';
      
      if (!skipAttacks) {
        // Execute attacks
        for (const allocation of this.allocations) {
          if (allocation.units > 0) {
            await API.risk.executeMove({
              activity_id: this.activityId,
              move_type: 'attack',
              to_territory_id: allocation.territoryId,
              units: allocation.units,
              km: allocation.units // Simplified
            });
          }
        }
      }
      
      // Show success and redirect
      this.showToast('¡Actividad registrada con éxito!', 'success');
      
      setTimeout(() => {
        window.location.href = '/';
      }, 1500);
      
    } catch (error) {
      console.error('Error confirming activity:', error);
      this.showToast('Error al guardar', 'error');
      
      const btnConfirm = document.getElementById('btn-confirm');
      btnConfirm.disabled = false;
      btnConfirm.textContent = '✅ Confirmar Ataques';
    }
  }
  
  formatDuration(minutes) {
    const mins = Math.floor(minutes);
    const secs = Math.floor((minutes - mins) * 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
  
  calculatePace(activity) {
    const pace = activity.duration_minutes / activity.distance_km;
    const paceMin = Math.floor(pace);
    const paceSec = Math.floor((pace - paceMin) * 60);
    return `${paceMin}'${paceSec.toString().padStart(2, '0')}"`;
  }
  
  showToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span>${type === 'success' ? '✓' : '✕'}</span>
      <span>${message}</span>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.remove(), 3000);
  }
}
