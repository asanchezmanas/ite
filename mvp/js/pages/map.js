// js/pages/map.js
import Store from '../core/store.js';
import API from '../core/api.js';
import MapService from '../services/map.js';

export default class MapPage {
  constructor() {
    this.map = null;
    this.territories = [];
    this.selectedTerritory = null;
  }
  
  async render(container) {
    container.innerHTML = `
      <div class="map-page">
        <!-- Top Bar -->
        <div class="top-bar">
          <button class="btn-back" onclick="window.history.back()">←</button>
          <h1>Mapa de Conquista</h1>
          <button class="btn-icon" id="btn-filter">⚙️</button>
        </div>
        
        <!-- Map Container -->
        <div id="map" style="height: calc(100vh - 136px); width: 100%;"></div>
        
        <!-- Zoom Controls -->
        <div style="position: absolute; top: 80px; right: 16px; z-index: 1000; display: flex; flex-direction: column; gap: 8px;">
          <button class="btn btn-icon" id="zoom-in" style="background: var(--bg-primary); box-shadow: var(--shadow-md);">+</button>
          <button class="btn btn-icon" id="zoom-out" style="background: var(--bg-primary); box-shadow: var(--shadow-md);">−</button>
          <button class="btn btn-icon" id="locate-me" style="background: var(--bg-primary); box-shadow: var(--shadow-md);">📍</button>
        </div>
        
        <!-- Legend -->
        <div class="map-legend" style="position: absolute; bottom: 96px; left: 16px; background: var(--bg-primary); padding: 12px; border-radius: var(--radius-lg); box-shadow: var(--shadow-md); font-size: 12px;">
          <div style="display: flex; gap: 12px; align-items: center;">
            <span style="width: 16px; height: 16px; background: var(--brand-500); border-radius: 4px;"></span>
            <span>Tu equipo</span>
          </div>
          <div style="display: flex; gap: 12px; align-items: center; margin-top: 8px;">
            <span style="width: 16px; height: 16px; background: var(--error-500); border-radius: 4px;"></span>
            <span>Enemigo</span>
          </div>
          <div style="display: flex; gap: 12px; align-items: center; margin-top: 8px;">
            <span style="width: 16px; height: 16px; background: var(--gray-400); border-radius: 4px;"></span>
            <span>Neutral</span>
          </div>
        </div>
      </div>
      
      <!-- Territory Modal -->
      <div id="territory-modal" style="display: none;"></div>
    `;
    
    await this.initMap();
    this.attachEvents();
  }
  
  async initMap() {
    // Initialize Leaflet map
    this.map = L.map('map', {
      center: [41.3851, 2.1734], // Barcelona
      zoom: 13,
      zoomControl: false
    });
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18
    }).addTo(this.map);
    
    // Load territories
    await this.loadTerritories();
  }
  
  async loadTerritories() {
    try {
      const data = await API.risk.getMap('city', 41.3851, 2.1734);
      this.territories = data.territories || [];
      
      // Render hexagons
      this.renderHexagons();
      
    } catch (error) {
      console.error('Error loading map:', error);
      this.showToast('Error al cargar mapa', 'error');
    }
  }
  
  renderHexagons() {
    this.territories.forEach(territory => {
      // Get H3 hexagons from territory
      const hexagons = territory.h3_indexes || [];
      
      hexagons.forEach(h3Index => {
        // Convert H3 to geographic boundary
        const boundary = h3.cellToBoundary(h3Index);
        const latlngs = boundary.map(coord => [coord[0], coord[1]]);
        
        // Determine color
        let color = '#98a2b3'; // Neutral gray
        if (territory.controller_team_id === Store.getState('user.team_id')) {
          color = '#465fff'; // Brand blue
        } else if (territory.controller_team_id) {
          color = '#f04438'; // Error red
        }
        
        // Create polygon
        const polygon = L.polygon(latlngs, {
          color: territory.is_under_attack ? '#f79009' : color,
          fillColor: color,
          fillOpacity: 0.4,
          weight: territory.is_under_attack ? 2 : 1
        }).addTo(this.map);
        
        // Add popup
        polygon.bindPopup(this.createPopupContent(territory));
        
        // Click event
        polygon.on('click', () => {
          this.showTerritoryModal(territory);
        });
      });
    });
  }
  
  createPopupContent(territory) {
    return `
      <div style="font-family: var(--font-family); min-width: 200px;">
        <h3 style="margin-bottom: 8px;">${territory.name}</h3>
        <p style="color: var(--text-secondary); font-size: 14px; margin-bottom: 12px;">
          ${territory.controller_name || 'Neutral'}
        </p>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
          <span style="color: var(--text-secondary);">Unidades:</span>
          <strong>${territory.units || 0}</strong>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span style="color: var(--text-secondary);">Control:</span>
          <strong>${territory.days_controlled || 0} días</strong>
        </div>
        ${territory.is_under_attack ? `
          <div style="margin-top: 12px; padding: 8px; background: var(--warning-50); border-radius: 6px; color: var(--warning-500); font-size: 12px; font-weight: 500;">
            ⚔️ Bajo ataque
          </div>
        ` : ''}
      </div>
    `;
  }
  
  showTerritoryModal(territory) {
    this.selectedTerritory = territory;
    
    const modal = document.getElementById('territory-modal');
    const isMyTerritory = territory.controller_team_id === Store.getState('user.team_id');
    
    modal.innerHTML = `
      <div class="modal-overlay" onclick="this.parentElement.style.display='none'">
        <div class="modal" onclick="event.stopPropagation()">
          <div class="modal-header">
            <h2>${territory.name}</h2>
            <button class="btn-icon" onclick="document.getElementById('territory-modal').style.display='none'">✕</button>
          </div>
          
          <div class="card" style="margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
              <span style="color: var(--text-secondary);">Controlador</span>
              <strong>${territory.controller_flag || ''} ${territory.controller_name || 'Neutral'}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
              <span style="color: var(--text-secondary);">Unidades</span>
              <strong style="color: var(--brand-500);">${territory.units || 0}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
              <span style="color: var(--text-secondary);">Días controlados</span>
              <strong>${territory.days_controlled || 0}</strong>
            </div>
            ${territory.defense_bonus ? `
              <div style="display: flex; justify-content: space-between;">
                <span style="color: var(--text-secondary);">Bonus defensa</span>
                <strong style="color: var(--success-500);">+${territory.defense_bonus * 100}%</strong>
              </div>
            ` : ''}
          </div>
          
          ${territory.is_under_attack ? `
            <div class="card" style="border-left: 4px solid var(--warning-500); margin-bottom: 16px;">
              <h3 style="margin-bottom: 8px;">⚔️ Batalla Activa</h3>
              <p style="color: var(--text-secondary); margin-bottom: 12px;">
                ${territory.attacker_name} está atacando
              </p>
              <div style="background: var(--gray-100); border-radius: var(--radius-md); height: 8px; overflow: hidden;">
                <div style="background: var(--warning-500); height: 100%; width: ${territory.battle_progress}%;"></div>
              </div>
              <p style="text-align: center; margin-top: 8px; font-size: 12px; color: var(--text-secondary);">
                ${territory.battle_progress}% hacia conquista
              </p>
            </div>
          ` : ''}
          
          <div style="display: flex; gap: 12px;">
            ${isMyTerritory ? `
              <button class="btn btn-secondary" style="flex: 1;" onclick="alert('Función de defensa en desarrollo')">
                🛡️ Defender
              </button>
            ` : `
              <button class="btn btn-primary" style="flex: 1;" onclick="alert('Registra una actividad primero')">
                ⚔️ Atacar
              </button>
            `}
            <button class="btn btn-secondary" onclick="document.getElementById('territory-modal').style.display='none'">
              Cerrar
            </button>
          </div>
        </div>
      </div>
    `;
    
    modal.style.display = 'block';
  }
  
  attachEvents() {
    document.getElementById('zoom-in').addEventListener('click', () => {
      this.map.zoomIn();
    });
    
    document.getElementById('zoom-out').addEventListener('click', () => {
      this.map.zoomOut();
    });
    
    document.getElementById('locate-me').addEventListener('click', async () => {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const { latitude, longitude } = position.coords;
            this.map.setView([latitude, longitude], 15);
            
            // Add marker
            L.marker([latitude, longitude], {
              icon: L.divIcon({
                className: 'user-marker',
                html: '<div style="width: 20px; height: 20px; background: var(--brand-500); border: 3px solid white; border-radius: 50%; box-shadow: var(--shadow-md);"></div>'
              })
            }).addTo(this.map);
          },
          (error) => {
            this.showToast('No se pudo obtener ubicación', 'error');
          }
        );
      }
    });
  }
  
  showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span>${type === 'success' ? '✓' : '✕'}</span>
      <span>${message}</span>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.style.animation = 'fadeOut 0.3s';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }
  
  destroy() {
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
  }
}
