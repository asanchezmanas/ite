// js/pages/tracking.js
import Store from '../core/store.js';
import API from '../core/api.js';
import LocationService from '../services/location.js';

export default class TrackingPage {
  constructor() {
    this.isTracking = false;
    this.startTime = null;
    this.distance = 0;
    this.points = [];
    this.hexagons = new Set();
  }
  
  async render(container) {
    container.innerHTML = `
      <div class="tracking-page">
        <div class="tracking-header">
          <button class="btn-back" onclick="window.history.back()">←</button>
          <h1>Entrenamiento</h1>
        </div>
        
        <div class="tracking-stats">
          <div class="stat-main">
            <div class="stat-value" id="distance">0.00</div>
            <div class="stat-label">km</div>
          </div>
          
          <div class="stat-row">
            <div class="stat">
              <div class="stat-value" id="duration">00:00</div>
              <div class="stat-label">Tiempo</div>
            </div>
            <div class="stat">
              <div class="stat-value" id="pace">0'00"</div>
              <div class="stat-label">Pace</div>
            </div>
          </div>
          
          <div class="hexagon-counter">
            🗺️ <span id="hexagons">0</span> hexágonos
          </div>
        </div>
        
        <div class="tracking-actions">
          <button id="btn-start" class="btn-primary btn-large">
            ▶️ INICIAR
          </button>
          <button id="btn-pause" class="btn-secondary btn-large" style="display:none">
            ⏸️ PAUSAR
          </button>
          <button id="btn-stop" class="btn-danger" style="display:none">
            ⏹️ TERMINAR
          </button>
        </div>
        
        <div class="tracking-info">
          💾 Se guarda automáticamente cada 30s
        </div>
      </div>
    `;
    
    this.attachEvents();
  }
  
  attachEvents() {
    document.getElementById('btn-start').addEventListener('click', () => this.start());
    document.getElementById('btn-pause').addEventListener('click', () => this.pause());
    document.getElementById('btn-stop').addEventListener('click', () => this.stop());
  }
  
  async start() {
    try {
      await LocationService.startTracking(this.onLocationUpdate.bind(this));
      
      this.isTracking = true;
      this.startTime = Date.now();
      this.updateUI();
      
      // Start timer
      this.timer = setInterval(() => this.updateDuration(), 1000);
      
      document.getElementById('btn-start').style.display = 'none';
      document.getElementById('btn-pause').style.display = 'block';
      document.getElementById('btn-stop').style.display = 'block';
    } catch (error) {
      alert('No se pudo acceder al GPS: ' + error.message);
    }
  }
  
  pause() {
    this.isTracking = false;
    LocationService.stopTracking();
    clearInterval(this.timer);
    
    document.getElementById('btn-pause').textContent = '▶️ REANUDAR';
    document.getElementById('btn-pause').onclick = () => this.start();
  }
  
  async stop() {
    this.isTracking = false;
    LocationService.stopTracking();
    clearInterval(this.timer);
    
    // Save activity
    const activity = {
      distance_km: this.distance,
      duration_minutes: (Date.now() - this.startTime) / 60000,
      activity_type: 'run',
      recorded_at: new Date(this.startTime).toISOString(),
      h3_indexes: Array.from(this.hexagons)
    };
    
    try {
      const result = await API.activities.create(activity);
      // Navigate to distribution page
      window.location.href = `/activity/${result.id}/distribute`;
    } catch (error) {
      alert('Error al guardar: ' + error.message);
    }
  }
  
  onLocationUpdate(position) {
    if (!this.isTracking) return;
    
    const { latitude, longitude } = position.coords;
    
    // Add point
    this.points.push({ lat: latitude, lng: longitude, time: Date.now() });
    
    // Calculate distance
    if (this.points.length > 1) {
      const last = this.points[this.points.length - 2];
      const current = this.points[this.points.length - 1];
      this.distance += this.calculateDistance(last, current);
    }
    
    // Detect hexagon (using h3-js)
    const h3Index = h3.latLngToCell(latitude, longitude, 9);
    this.hexagons.add(h3Index);
    
    this.updateUI();
  }
  
  calculateDistance(point1, point2) {
    // Haversine formula
    const R = 6371; // Earth radius in km
    const dLat = (point2.lat - point1.lat) * Math.PI / 180;
    const dLon = (point2.lng - point1.lng) * Math.PI / 180;
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(point1.lat * Math.PI / 180) * Math.cos(point2.lat * Math.PI / 180) *
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  }
  
  updateDuration() {
    const seconds = Math.floor((Date.now() - this.startTime) / 1000);
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    document.getElementById('duration').textContent = 
      `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  
  updateUI() {
    document.getElementById('distance').textContent = this.distance.toFixed(2);
    document.getElementById('hexagons').textContent = this.hexagons.size;
    
    // Calculate pace
    if (this.distance > 0) {
      const durationMins = (Date.now() - this.startTime) / 60000;
      const pace = durationMins / this.distance;
      const paceMin = Math.floor(pace);
      const paceSec = Math.floor((pace - paceMin) * 60);
      document.getElementById('pace').textContent = 
        `${paceMin}'${paceSec.toString().padStart(2, '0')}"`;
    }
  }
  
  destroy() {
    LocationService.stopTracking();
    clearInterval(this.timer);
  }
}
