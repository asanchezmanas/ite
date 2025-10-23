// js/services/analytics.js

class AnalyticsService {
  constructor() {
    this.userId = null;
    this.sessionId = this.generateSessionId();
    this.queue = [];
    this.isOnline = navigator.onLine;
    this.batchSize = 10;
    this.flushInterval = 30000; // 30 segundos
    
    // Auto flush
    setInterval(() => this.flush(), this.flushInterval);
    
    // Flush on page unload
    window.addEventListener('beforeunload', () => this.flush());
    
    // Network status
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.flush();
    });
    
    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }
  
  // Initialize with user ID
  init(userId) {
    this.userId = userId;
    this.track('session_start', {
      platform: this.getPlatform(),
      screen_size: `${window.innerWidth}x${window.innerHeight}`,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
    });
  }
  
  // Track event
  track(eventName, properties = {}) {
    const event = {
      event_name: eventName,
      user_id: this.userId,
      session_id: this.sessionId,
      timestamp: new Date().toISOString(),
      properties: {
        ...properties,
        url: window.location.pathname,
        referrer: document.referrer,
        user_agent: navigator.userAgent
      }
    };
    
    console.log('📊 Analytics:', eventName, properties);
    
    this.queue.push(event);
    
    // Auto flush if queue is full
    if (this.queue.length >= this.batchSize) {
      this.flush();
    }
  }
  
  // Flush queue to server
  async flush() {
    if (this.queue.length === 0 || !this.isOnline) {
      return;
    }
    
    const events = [...this.queue];
    this.queue = [];
    
    try {
      await fetch('/api/analytics/batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({ events })
      });
      
      console.log('✅ Analytics flushed:', events.length, 'events');
      
    } catch (error) {
      console.error('❌ Analytics flush failed:', error);
      // Re-queue events
      this.queue.unshift(...events);
    }
  }
  
  // Page view
  page(pageName, properties = {}) {
    this.track('page_view', {
      page_name: pageName,
      ...properties
    });
  }
  
  // Timing event
  time(eventName, startTime) {
    const duration = Date.now() - startTime;
    this.track(eventName, { duration_ms: duration });
  }
  
  // Helper methods
  generateSessionId() {
    return `${Date.now()}-${Math.random().toString(36).substring(7)}`;
  }
  
  getPlatform() {
    const ua = navigator.userAgent;
    if (/android/i.test(ua)) return 'android';
    if (/iPad|iPhone|iPod/.test(ua)) return 'ios';
    return 'web';
  }
}

export default new AnalyticsService();

// ============================================
// PREDEFINED EVENTS
// ============================================

export const Events = {
  // Auth
  SIGNUP: 'signup',
  LOGIN: 'login',
  LOGOUT: 'logout',
  
  // Activity
  ACTIVITY_STARTED: 'activity_started',
  ACTIVITY_PAUSED: 'activity_paused',
  ACTIVITY_RESUMED: 'activity_resumed',
  ACTIVITY_COMPLETED: 'activity_completed',
  ACTIVITY_SAVED: 'activity_saved',
  
  // RISK/Conquest
  TERRITORY_VIEWED: 'territory_viewed',
  TERRITORY_ATTACKED: 'territory_attacked',
  TERRITORY_DEFENDED: 'territory_defended',
  TERRITORY_CONQUERED: 'territory_conquered',
  TERRITORY_LOST: 'territory_lost',
  
  // Battle
  BATTLE_VIEWED: 'battle_viewed',
  BATTLE_JOINED: 'battle_joined',
  BATTLE_WON: 'battle_won',
  BATTLE_LOST: 'battle_lost',
  
  // Social
  TEAM_CREATED: 'team_created',
  TEAM_JOINED: 'team_joined',
  TEAM_LEFT: 'team_left',
  TEAM_INVITE_SENT: 'team_invite_sent',
  
  // Engagement
  MAP_OPENED: 'map_opened',
  MAP_ZOOMED: 'map_zoomed',
  PROFILE_VIEWED: 'profile_viewed',
  RANKINGS_VIEWED: 'rankings_viewed',
  ACHIEVEMENT_UNLOCKED: 'achievement_unlocked',
  
  // Integration
  STRAVA_CONNECTED: 'strava_connected',
  STRAVA_DISCONNECTED: 'strava_disconnected',
  STRAVA_ACTIVITY_SYNCED: 'strava_activity_synced',
  
  // Errors
  ERROR_OCCURRED: 'error_occurred',
  API_ERROR: 'api_error',
  GPS_ERROR: 'gps_error'
};
