// js/core/analytics.js
import AnalyticsService, { Events } from '../services/analytics.js';
import Store from './store.js';

class Analytics {
  // Easy tracking methods
  static trackActivity(action, distance, duration) {
    AnalyticsService.track(Events.ACTIVITY_COMPLETED, {
      action,
      distance_km: distance,
      duration_minutes: duration,
      activity_type: 'run'
    });
  }
  
  static trackConquest(territoryId, territoryName, success) {
    AnalyticsService.track(
      success ? Events.TERRITORY_CONQUERED : Events.TERRITORY_ATTACKED,
      {
        territory_id: territoryId,
        territory_name: territoryName,
        success
      }
    );
  }
  
  static trackBattle(battleId, action) {
    AnalyticsService.track(Events.BATTLE_VIEWED, {
      battle_id: battleId,
      action
    });
  }
  
  static trackError(error, context = {}) {
    AnalyticsService.track(Events.ERROR_OCCURRED, {
      error_message: error.message,
      error_stack: error.stack,
      ...context
    });
  }
  
  static trackPageTiming(pageName, startTime) {
    AnalyticsService.time(`${pageName}_load_time`, startTime);
  }
  
  // User properties
  static setUser(userId, properties = {}) {
    AnalyticsService.init(userId);
    AnalyticsService.track('user_properties_set', properties);
  }
  
  // Convenience methods
  static pageView(pageName) {
    AnalyticsService.page(pageName);
  }
  
  static track(eventName, properties) {
    AnalyticsService.track(eventName, properties);
  }
}

export default Analytics;
