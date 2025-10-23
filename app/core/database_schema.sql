-- Ejecutar esto en el SQL Editor de Supabase

-- Enable PostGIS para geolocalización
CREATE EXTENSION IF NOT EXISTS postgis;

-- ==========================================
-- USUARIOS
-- ==========================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    
    -- Stats
    total_km DECIMAL(10, 2) DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    zones_controlled INTEGER DEFAULT 0,
    
    -- Team
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    
    -- Integrations
    strava_athlete_id BIGINT UNIQUE,
    strava_access_token TEXT,
    strava_refresh_token TEXT,
    strava_token_expires_at TIMESTAMPTZ,
    
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- EQUIPOS
-- ==========================================
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#3B82F6', -- Hex color
    logo_url TEXT,
    
    -- Stats
    total_km DECIMAL(10, 2) DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    zones_controlled INTEGER DEFAULT 0,
    members_count INTEGER DEFAULT 0,
    
    -- Config
    is_public BOOLEAN DEFAULT TRUE,
    max_members INTEGER DEFAULT 50,
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- ZONAS (Hexágonos H3)
-- ==========================================
CREATE TABLE zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    h3_index VARCHAR(20) UNIQUE NOT NULL, -- Índice H3
    
    -- Ubicación
    center_lat DECIMAL(10, 8) NOT NULL,
    center_lng DECIMAL(11, 8) NOT NULL,
    city VARCHAR(100),
    district VARCHAR(100),
    
    -- Control
    controlled_by_team UUID REFERENCES teams(id) ON DELETE SET NULL,
    controlled_by_user UUID REFERENCES users(id) ON DELETE SET NULL,
    control_percentage DECIMAL(5, 2) DEFAULT 0, -- 0-100%
    
    -- Stats
    total_km DECIMAL(10, 2) DEFAULT 0,
    total_activities INTEGER DEFAULT 0,
    
    -- Points of Interest (opcional)
    is_poi BOOLEAN DEFAULT FALSE,
    poi_type VARCHAR(50), -- park, monument, gym, stadium
    poi_name VARCHAR(255),
    bonus_multiplier DECIMAL(3, 2) DEFAULT 1.0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_zones_h3 ON zones(h3_index);
CREATE INDEX idx_zones_team ON zones(controlled_by_team);
CREATE INDEX idx_zones_city ON zones(city);

-- ==========================================
-- ACTIVIDADES
-- ==========================================
CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    
    -- Datos actividad
    activity_type VARCHAR(50) DEFAULT 'run', -- run, walk, bike, gym
    distance_km DECIMAL(10, 2) NOT NULL,
    duration_minutes INTEGER,
    avg_pace DECIMAL(5, 2), -- min/km
    calories INTEGER,
    elevation_gain INTEGER, -- metros
    
    -- Geolocalización
    start_lat DECIMAL(10, 8),
    start_lng DECIMAL(11, 8),
    polyline TEXT, -- Encoded polyline de Google
    
    -- Gym activities
    is_gym_activity BOOLEAN DEFAULT FALSE,
    assigned_zones TEXT[], -- Array de H3 indexes si es gym
    
    -- Source
    source VARCHAR(50) DEFAULT 'manual', -- manual, strava, garmin
    external_id VARCHAR(255), -- ID de Strava/Garmin
    
    -- Points
    points_earned INTEGER DEFAULT 0,
    
    recorded_at TIMESTAMPTZ NOT NULL,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_activities_user ON activities(user_id);
CREATE INDEX idx_activities_team ON activities(team_id);
CREATE INDEX idx_activities_recorded ON activities(recorded_at DESC);
CREATE INDEX idx_activities_external ON activities(source, external_id);

-- ==========================================
-- ACTIVIDAD POR ZONA
-- ==========================================
CREATE TABLE zone_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    
    -- Distancia en esta zona específica
    distance_km DECIMAL(10, 2) NOT NULL,
    points_earned INTEGER DEFAULT 0,
    
    recorded_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(zone_id, activity_id)
);

CREATE INDEX idx_zone_activities_zone ON zone_activities(zone_id);
CREATE INDEX idx_zone_activities_user ON zone_activities(user_id);
CREATE INDEX idx_zone_activities_team ON zone_activities(team_id);
CREATE INDEX idx_zone_activities_recorded ON zone_activities(recorded_at DESC);

-- ==========================================
-- HISTORIAL DE CONTROL DE ZONAS
-- ==========================================
CREATE TABLE zone_control_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    
    -- Cambio de control
    previous_team UUID REFERENCES teams(id),
    previous_user UUID REFERENCES users(id),
    new_team UUID REFERENCES teams(id),
    new_user UUID REFERENCES users(id),
    
    -- Context
    trigger_activity_id UUID REFERENCES activities(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_zone_history_zone ON zone_control_history(zone_id);
CREATE INDEX idx_zone_history_created ON zone_control_history(created_at DESC);

-- ==========================================
-- LOGROS/ACHIEVEMENTS
-- ==========================================
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_url TEXT,
    
    -- Requerimientos
    requirement_type VARCHAR(50), -- total_km, zones_controlled, activities_count
    requirement_value INTEGER,
    
    points_reward INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    
    unlocked_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, achievement_id)
);

-- ==========================================
-- FUNCIONES Y TRIGGERS
-- ==========================================

-- Actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_zones_updated_at BEFORE UPDATE ON zones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Actualizar stats del usuario cuando se crea actividad
CREATE OR REPLACE FUNCTION update_user_stats_on_activity()
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

CREATE TRIGGER trigger_update_user_stats AFTER INSERT ON activities
    FOR EACH ROW EXECUTE FUNCTION update_user_stats_on_activity();

-- Actualizar stats del equipo cuando se crea actividad
CREATE OR REPLACE FUNCTION update_team_stats_on_activity()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.team_id IS NOT NULL THEN
        UPDATE teams
        SET 
            total_km = total_km + NEW.distance_km,
            total_points = total_points + NEW.points_earned,
            updated_at = NOW()
        WHERE id = NEW.team_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_team_stats AFTER INSERT ON activities
    FOR EACH ROW EXECUTE FUNCTION update_team_stats_on_activity();

-- Actualizar contador de miembros del equipo
CREATE OR REPLACE FUNCTION update_team_members_count()
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

CREATE TRIGGER trigger_update_team_members AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION update_team_members_count();

-- ==========================================
-- DATOS INICIALES
-- ==========================================

-- Logros básicos
INSERT INTO achievements (code, name, description, requirement_type, requirement_value, points_reward) VALUES
('first_steps', 'Primeros Pasos', 'Completa tu primera actividad', 'activities_count', 1, 10),
('runner_5k', 'Corredor 5K', 'Acumula 5 km en total', 'total_km', 5, 25),
('runner_10k', 'Corredor 10K', 'Acumula 10 km en total', 'total_km', 10, 50),
('runner_marathon', 'Maratoniano', 'Acumula 42 km en total', 'total_km', 42, 200),
('zone_conqueror', 'Conquistador', 'Controla tu primera zona', 'zones_controlled', 1, 50),
('zone_master', 'Maestro del Territorio', 'Controla 10 zonas', 'zones_controlled', 10, 500);

-- Row Level Security (RLS) - Seguridad básica
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;

-- Política: usuarios pueden ver sus propios datos
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Política: actividades visibles por su dueño y admin
CREATE POLICY "Users can view own activities" ON activities
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own activities" ON activities
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- Zonas son públicas (todos pueden ver)
CREATE POLICY "Zones are public" ON zones
    FOR SELECT USING (true);