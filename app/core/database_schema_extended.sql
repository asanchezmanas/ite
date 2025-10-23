-- EXTENSIÓN DEL SCHEMA PARA MULTI-ESCALA
-- Ejecutar DESPUÉS de database_schema.sql

-- ==========================================
-- COMPETICIONES (Challenges/Batallas)
-- ==========================================
CREATE TYPE competition_scope AS ENUM ('zone', 'district', 'city', 'region', 'country', 'global');
CREATE TYPE competition_status AS ENUM ('upcoming', 'active', 'finished');

CREATE TABLE competitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Scope y objetivos
    scope competition_scope NOT NULL,
    target_entity VARCHAR(100), -- nombre de ciudad/país/etc
    
    -- Participantes
    participant_type VARCHAR(50) DEFAULT 'individual', -- individual, team, city, country
    min_participants INTEGER DEFAULT 2,
    max_participants INTEGER,
    
    -- Timing
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    status competition_status DEFAULT 'upcoming',
    
    -- Premios
    prize_pool DECIMAL(10, 2) DEFAULT 0,
    has_achievements BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    image_url TEXT,
    rules JSONB, -- reglas personalizables
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_competitions_status ON competitions(status);
CREATE INDEX idx_competitions_scope ON competitions(scope);
CREATE INDEX idx_competitions_dates ON competitions(start_date, end_date);

-- ==========================================
-- PARTICIPANTES EN COMPETICIONES
-- ==========================================
CREATE TABLE competition_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competition_id UUID NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    
    -- Puede ser usuario, equipo, ciudad, etc
    participant_type VARCHAR(50) NOT NULL, -- user, team, city, country
    participant_id UUID, -- user_id o team_id
    participant_name VARCHAR(255), -- nombre de ciudad/país si aplica
    
    -- Stats en esta competición
    total_km DECIMAL(10, 2) DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    activities_count INTEGER DEFAULT 0,
    
    -- Posición
    current_rank INTEGER,
    
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(competition_id, participant_type, participant_id, participant_name)
);

CREATE INDEX idx_comp_participants_competition ON competition_participants(competition_id);
CREATE INDEX idx_comp_participants_rank ON competition_participants(competition_id, current_rank);

-- ==========================================
-- ASIGNACIÓN DE KM A COMPETICIONES
-- ==========================================
CREATE TABLE activity_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    competition_id UUID NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    
    -- Asignación
    allocated_km DECIMAL(10, 2) NOT NULL CHECK (allocated_km >= 0),
    allocated_percentage DECIMAL(5, 2), -- % del total
    
    -- Points earned específicos de esta competición
    points_earned INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(activity_id, competition_id)
);

CREATE INDEX idx_allocations_activity ON activity_allocations(activity_id);
CREATE INDEX idx_allocations_competition ON activity_allocations(competition_id);

-- ==========================================
-- CIUDADES Y REGIONES (Entidades geográficas)
-- ==========================================
CREATE TABLE geographic_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    entity_type competition_scope NOT NULL, -- district, city, region, country
    
    -- Jerarquía
    parent_id UUID REFERENCES geographic_entities(id), -- ciudad -> región -> país
    
    -- Ubicación
    center_lat DECIMAL(10, 8),
    center_lng DECIMAL(11, 8),
    
    -- Stats globales
    total_zones INTEGER DEFAULT 0,
    total_users INTEGER DEFAULT 0,
    total_teams INTEGER DEFAULT 0,
    total_km DECIMAL(12, 2) DEFAULT 0,
    
    -- Control actual
    controlled_by_team UUID REFERENCES teams(id),
    controlled_by_city VARCHAR(255), -- nombre de ciudad ganadora
    controlled_by_country VARCHAR(255),
    control_percentage DECIMAL(5, 2) DEFAULT 0,
    
    -- Metadata
    flag_emoji VARCHAR(10), -- 🇪🇸, 🇫🇷
    color VARCHAR(7) DEFAULT '#3B82F6',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(name, entity_type)
);

CREATE INDEX idx_geo_entities_type ON geographic_entities(entity_type);
CREATE INDEX idx_geo_entities_parent ON geographic_entities(parent_id);

-- Vincular zonas a entidades geográficas
ALTER TABLE zones ADD COLUMN district_id UUID REFERENCES geographic_entities(id);
ALTER TABLE zones ADD COLUMN city_id UUID REFERENCES geographic_entities(id);
ALTER TABLE zones ADD COLUMN region_id UUID REFERENCES geographic_entities(id);
ALTER TABLE zones ADD COLUMN country_id UUID REFERENCES geographic_entities(id);

-- ==========================================
-- STATS DE USUARIOS POR ENTIDAD GEOGRÁFICA
-- ==========================================
CREATE TABLE user_geographic_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entity_id UUID NOT NULL REFERENCES geographic_entities(id) ON DELETE CASCADE,
    
    -- Stats
    total_km DECIMAL(10, 2) DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    activities_count INTEGER DEFAULT 0,
    rank_in_entity INTEGER,
    
    last_activity_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, entity_id)
);

CREATE INDEX idx_user_geo_stats_user ON user_geographic_stats(user_id);
CREATE INDEX idx_user_geo_stats_entity ON user_geographic_stats(entity_id);
CREATE INDEX idx_user_geo_stats_rank ON user_geographic_stats(entity_id, rank_in_entity);

-- ==========================================
-- TRIGGERS Y FUNCIONES
-- ==========================================

-- Actualizar stats de participante cuando se asignan KM
CREATE OR REPLACE FUNCTION update_competition_participant_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Obtener info de actividad
    WITH activity_info AS (
        SELECT user_id, team_id 
        FROM activities 
        WHERE id = NEW.activity_id
    )
    UPDATE competition_participants cp
    SET 
        total_km = total_km + NEW.allocated_km,
        total_points = total_points + NEW.points_earned,
        activities_count = activities_count + 1
    FROM activity_info ai
    WHERE cp.competition_id = NEW.competition_id
    AND (
        (cp.participant_type = 'user' AND cp.participant_id = ai.user_id)
        OR (cp.participant_type = 'team' AND cp.participant_id = ai.team_id)
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_comp_stats 
AFTER INSERT ON activity_allocations
FOR EACH ROW EXECUTE FUNCTION update_competition_participant_stats();

-- Actualizar status de competiciones automáticamente
CREATE OR REPLACE FUNCTION update_competition_status()
RETURNS void AS $$
BEGIN
    -- Marcar como activas
    UPDATE competitions
    SET status = 'active'
    WHERE status = 'upcoming'
    AND start_date <= NOW();
    
    -- Marcar como finalizadas
    UPDATE competitions
    SET status = 'finished'
    WHERE status = 'active'
    AND end_date <= NOW();
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- DATOS INICIALES - ENTIDADES GEOGRÁFICAS
-- ==========================================

-- España
INSERT INTO geographic_entities (name, entity_type, flag_emoji, color) VALUES
('España', 'country', '🇪🇸', '#C60B1E');

-- Cataluña
INSERT INTO geographic_entities (name, entity_type, parent_id, flag_emoji) VALUES
('Cataluña', 'region', (SELECT id FROM geographic_entities WHERE name = 'España' LIMIT 1), '🏴');

-- Ciudades de Cataluña
WITH catalunya AS (SELECT id FROM geographic_entities WHERE name = 'Cataluña' LIMIT 1)
INSERT INTO geographic_entities (name, entity_type, parent_id, center_lat, center_lng) VALUES
('Barcelona', 'city', (SELECT id FROM catalunya), 41.3851, 2.1734),
('Badalona', 'city', (SELECT id FROM catalunya), 41.4501, 2.2467),
('Hospitalet de Llobregat', 'city', (SELECT id FROM catalunya), 41.3596, 2.1000),
('Terrassa', 'city', (SELECT id FROM catalunya), 41.5633, 2.0099),
('Sabadell', 'city', (SELECT id FROM catalunya), 41.5433, 2.1082);

-- Francia
INSERT INTO geographic_entities (name, entity_type, flag_emoji, color) VALUES
('Francia', 'country', '🇫🇷', '#0055A4');

-- ==========================================
-- VISTAS ÚTILES
-- ==========================================

-- Vista de competiciones activas con participantes
CREATE VIEW v_active_competitions AS
SELECT 
    c.*,
    COUNT(DISTINCT cp.id) as participant_count,
    COALESCE(SUM(cp.total_km), 0) as total_km_competition,
    COALESCE(SUM(cp.activities_count), 0) as total_activities
FROM competitions c
LEFT JOIN competition_participants cp ON c.id = cp.competition_id
WHERE c.status = 'active'
GROUP BY c.id;

-- Vista de ranking por ciudad
CREATE VIEW v_city_rankings AS
SELECT 
    ge.name as city_name,
    ge.flag_emoji,
    ge.total_km,
    ge.total_users,
    ge.total_teams,
    RANK() OVER (ORDER BY ge.total_km DESC) as city_rank
FROM geographic_entities ge
WHERE ge.entity_type = 'city'
ORDER BY ge.total_km DESC;

-- Vista de ranking por país
CREATE VIEW v_country_rankings AS
SELECT 
    ge.name as country_name,
    ge.flag_emoji,
    ge.total_km,
    COUNT(DISTINCT ge_child.id) as cities_count,
    RANK() OVER (ORDER BY ge.total_km DESC) as country_rank
FROM geographic_entities ge
LEFT JOIN geographic_entities ge_child ON ge_child.parent_id = ge.id
WHERE ge.entity_type = 'country'
GROUP BY ge.id, ge.name, ge.flag_emoji, ge.total_km
ORDER BY ge.total_km DESC;
