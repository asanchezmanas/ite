-- ==========================================
-- MVP SCHEMA - Territory Conquest
-- Simplified for rapid validation
-- ==========================================

-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- ==========================================
-- 1. USERS (Simplified)
-- ==========================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    avatar_url TEXT,
    
    -- Basic Stats
    total_km DECIMAL(10, 2) DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    zones_count INTEGER DEFAULT 0,
    
    -- Team
    team_id UUID,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_team ON users(team_id);

-- ==========================================
-- 2. TEAMS (Basic)
-- ==========================================
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#3B82F6',
    
    -- Stats
    total_km DECIMAL(10, 2) DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    members_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- 3. ACTIVITIES (Core)
-- ==========================================
CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id),
    
    -- Basic Data
    distance_km DECIMAL(10, 2) NOT NULL,
    duration_minutes INTEGER,
    
    -- Location (single point for MVP)
    lat DECIMAL(10, 8) NOT NULL,
    lng DECIMAL(11, 8) NOT NULL,
    city VARCHAR(100),
    
    -- Points
    points_earned INTEGER DEFAULT 0,
    
    recorded_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_activities_user ON activities(user_id);
CREATE INDEX idx_activities_team ON activities(team_id);
CREATE INDEX idx_activities_date ON activities(recorded_at DESC);

-- ==========================================
-- 4. ZONES (H3 Hexagons - Single City)
-- ==========================================
CREATE TABLE zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    h3_index VARCHAR(20) UNIQUE NOT NULL,
    
    -- Location
    center_lat DECIMAL(10, 8) NOT NULL,
    center_lng DECIMAL(11, 8) NOT NULL,
    city VARCHAR(100) NOT NULL,
    
    -- Control (simplified)
    controlled_by_team UUID REFERENCES teams(id),
    control_strength DECIMAL(10, 2) DEFAULT 0, -- KM accumulated
    
    -- Stats
    total_km DECIMAL(10, 2) DEFAULT 0,
    last_activity_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_zones_h3 ON zones(h3_index);
CREATE INDEX idx_zones_team ON zones(controlled_by_team);
CREATE INDEX idx_zones_city ON zones(city);

-- ==========================================
-- 5. ZONE_ACTIVITIES (Activity per Zone)
-- ==========================================
CREATE TABLE zone_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id),
    
    distance_km DECIMAL(10, 2) NOT NULL,
    points_earned INTEGER DEFAULT 0,
    
    recorded_at TIMESTAMPTZ NOT NULL,
    
    UNIQUE(zone_id, activity_id)
);

CREATE INDEX idx_zone_act_zone ON zone_activities(zone_id);
CREATE INDEX idx_zone_act_team ON zone_activities(team_id);

-- ==========================================
-- 6. CONTROL_HISTORY (Track Changes)
-- ==========================================
CREATE TABLE control_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID NOT NULL REFERENCES zones(id),
    previous_team UUID REFERENCES teams(id),
    new_team UUID NOT NULL REFERENCES teams(id),
    decisive_activity_id UUID REFERENCES activities(id),
    changed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_history_zone ON control_history(zone_id);
CREATE INDEX idx_history_date ON control_history(changed_at DESC);

-- ==========================================
-- TRIGGERS (Auto-update stats)
-- ==========================================

-- Update users stats on activity
CREATE OR REPLACE FUNCTION update_user_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE users
    SET 
        total_km = total_km + NEW.distance_km,
        total_points = total_points + NEW.points_earned,
        updated_at = NOW()
    WHERE id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_user_stats 
AFTER INSERT ON activities
FOR EACH ROW EXECUTE FUNCTION update_user_stats();

-- Update team stats on activity
CREATE OR REPLACE FUNCTION update_team_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.team_id IS NOT NULL THEN
        UPDATE teams
        SET 
            total_km = total_km + NEW.distance_km,
            total_points = total_points + NEW.points_earned
        WHERE id = NEW.team_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_team_stats 
AFTER INSERT ON activities
FOR EACH ROW EXECUTE FUNCTION update_team_stats();

-- Update team members count
CREATE OR REPLACE FUNCTION update_team_members()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.team_id IS NOT NULL THEN
        UPDATE teams SET members_count = members_count + 1 WHERE id = NEW.team_id;
    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.team_id IS NOT NULL AND OLD.team_id != NEW.team_id THEN
            UPDATE teams SET members_count = members_count - 1 WHERE id = OLD.team_id;
        END IF;
        IF NEW.team_id IS NOT NULL AND OLD.team_id != NEW.team_id THEN
            UPDATE teams SET members_count = members_count + 1 WHERE id = NEW.team_id;
        END IF;
    ELSIF TG_OP = 'DELETE' AND OLD.team_id IS NOT NULL THEN
        UPDATE teams SET members_count = members_count - 1 WHERE id = OLD.team_id;
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_team_members 
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION update_team_members();

-- ==========================================
-- VIEWS
-- ==========================================

-- Leaderboard users
CREATE VIEW v_leaderboard_users AS
SELECT 
    id,
    username,
    avatar_url,
    total_km,
    total_points,
    zones_count,
    team_id,
    RANK() OVER (ORDER BY total_points DESC) as rank
FROM users
WHERE is_active = TRUE;

-- Leaderboard teams
CREATE VIEW v_leaderboard_teams AS
SELECT 
    id,
    name,
    color,
    total_km,
    total_points,
    members_count,
    RANK() OVER (ORDER BY total_points DESC) as rank
FROM teams;

-- Zone control summary
CREATE VIEW v_zone_control AS
SELECT 
    z.id,
    z.h3_index,
    z.city,
    z.controlled_by_team,
    t.name as team_name,
    t.color as team_color,
    z.control_strength,
    z.total_km,
    z.last_activity_at
FROM zones z
LEFT JOIN teams t ON z.controlled_by_team = t.id;

-- ==========================================
-- SAMPLE DATA (for testing)
-- ==========================================

-- Insert sample city (Barcelona)
-- This would be populated by init script based on user's location
-- Example H3 indexes for Barcelona center would be added here
