-- SISTEMA MEJORADO: MULTI-CAPA CON HEXÁGONOS EN TODOS LOS NIVELES
-- Añadir a database_schema_extended.sql

-- ==========================================
-- HEXÁGONOS MULTI-ESCALA
-- ==========================================
-- Usar diferentes resoluciones H3 para cada nivel

ALTER TABLE geographic_entities ADD COLUMN h3_indexes TEXT[]; -- Array de hexágonos que componen la entidad
ALTER TABLE geographic_entities ADD COLUMN h3_resolution INTEGER; -- Resolución usada
ALTER TABLE geographic_entities ADD COLUMN boundary_geojson JSONB; -- Perímetro para visualización

-- Índice para búsquedas geoespaciales
CREATE INDEX idx_geo_entities_h3 ON geographic_entities USING GIN (h3_indexes);

-- ==========================================
-- SISTEMA DE FRONTERAS Y ATAQUES
-- ==========================================
CREATE TABLE border_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Entidades en conflicto
    entity_1_id UUID NOT NULL REFERENCES geographic_entities(id),
    entity_2_id UUID NOT NULL REFERENCES geographic_entities(id),
    
    -- Nivel (city-city, country-country, etc)
    border_type competition_scope NOT NULL,
    
    -- Zonas H3 en la frontera
    contested_h3_indexes TEXT[] NOT NULL,
    
    -- Control actual (% de hexágonos controlados)
    entity_1_control_pct DECIMAL(5, 2) DEFAULT 50,
    entity_2_control_pct DECIMAL(5, 2) DEFAULT 50,
    
    -- Stats
    total_battles INTEGER DEFAULT 0,
    last_battle_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(entity_1_id, entity_2_id, border_type)
);

CREATE INDEX idx_borders_entities ON border_zones(entity_1_id, entity_2_id);
CREATE INDEX idx_borders_type ON border_zones(border_type);

-- ==========================================
-- ATAQUES ESTRATÉGICOS
-- ==========================================
CREATE TABLE strategic_attacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Quién ataca
    attacker_id UUID NOT NULL REFERENCES users(id),
    attacker_team_id UUID REFERENCES teams(id),
    attacker_entity_id UUID REFERENCES geographic_entities(id), -- ciudad/país atacante
    
    -- Objetivo
    target_entity_id UUID NOT NULL REFERENCES geographic_entities(id),
    target_h3_indexes TEXT[], -- Hexágonos específicos atacados
    
    -- Recursos usados
    activity_id UUID NOT NULL REFERENCES activities(id),
    allocated_km DECIMAL(10, 2) NOT NULL,
    
    -- Resultado
    hexagons_conquered INTEGER DEFAULT 0,
    success_rate DECIMAL(5, 2), -- % de éxito
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_attacks_attacker ON strategic_attacks(attacker_id);
CREATE INDEX idx_attacks_target ON strategic_attacks(target_entity_id);
CREATE INDEX idx_attacks_created ON strategic_attacks(created_at DESC);

-- ==========================================
-- CONTROL HEXAGONAL POR ENTIDAD
-- ==========================================
CREATE TABLE entity_hexagon_control (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    h3_index VARCHAR(20) NOT NULL,
    h3_resolution INTEGER NOT NULL,
    
    -- Entidad geográfica (ciudad, país, etc)
    entity_id UUID NOT NULL REFERENCES geographic_entities(id),
    
    -- Control
    controlling_team UUID REFERENCES teams(id),
    controlling_user UUID REFERENCES users(id),
    control_strength DECIMAL(10, 2) DEFAULT 0, -- KM acumulados
    
    -- Stats últimos 30 días
    recent_km DECIMAL(10, 2) DEFAULT 0,
    recent_activities INTEGER DEFAULT 0,
    
    -- Disputa
    is_contested BOOLEAN DEFAULT FALSE,
    contested_by_entity UUID REFERENCES geographic_entities(id),
    
    last_activity_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(h3_index, entity_id)
);

CREATE INDEX idx_entity_hex_control_h3 ON entity_hexagon_control(h3_index);
CREATE INDEX idx_entity_hex_control_entity ON entity_hexagon_control(entity_id);
CREATE INDEX idx_entity_hex_control_contested ON entity_hexagon_control(is_contested) WHERE is_contested = TRUE;

-- ==========================================
-- DISTRIBUCIÓN AUTOMÁTICA DE KM
-- ==========================================
CREATE TABLE activity_layer_distribution (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    activity_id UUID NOT NULL REFERENCES activities(id),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Distribución por capa
    layer_type competition_scope NOT NULL, -- zone, city, region, country
    entity_id UUID NOT NULL REFERENCES geographic_entities(id),
    
    -- KM asignados
    auto_allocated_km DECIMAL(10, 2) DEFAULT 0, -- Defensa automática
    attack_allocated_km DECIMAL(10, 2) DEFAULT 0, -- Ataque manual
    
    -- Tipo de acción
    action_type VARCHAR(20) DEFAULT 'defend', -- defend, attack, neutral
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(activity_id, layer_type, entity_id)
);

CREATE INDEX idx_layer_dist_activity ON activity_layer_distribution(activity_id);
CREATE INDEX idx_layer_dist_entity ON activity_layer_distribution(entity_id);
CREATE INDEX idx_layer_dist_type ON activity_layer_distribution(layer_type);

-- ==========================================
-- FUNCIONES PARA DETECCIÓN AUTOMÁTICA
-- ==========================================

-- Función para distribuir KM automáticamente en todas las capas
CREATE OR REPLACE FUNCTION auto_distribute_activity_layers(
    p_activity_id UUID,
    p_user_id UUID,
    p_h3_indexes TEXT[],
    p_total_km DECIMAL
)
RETURNS void AS $$
DECLARE
    v_zone RECORD;
    v_entities UUID[];
    v_entity UUID;
    v_layer competition_scope;
BEGIN
    -- Obtener todas las entidades geográficas de las zonas atravesadas
    FOR v_zone IN 
        SELECT DISTINCT city_id, region_id, country_id
        FROM zones
        WHERE h3_index = ANY(p_h3_indexes)
    LOOP
        -- Ciudad
        IF v_zone.city_id IS NOT NULL THEN
            INSERT INTO activity_layer_distribution 
                (activity_id, user_id, layer_type, entity_id, auto_allocated_km, action_type)
            VALUES 
                (p_activity_id, p_user_id, 'city', v_zone.city_id, p_total_km, 'defend')
            ON CONFLICT (activity_id, layer_type, entity_id) DO NOTHING;
        END IF;
        
        -- Región
        IF v_zone.region_id IS NOT NULL THEN
            INSERT INTO activity_layer_distribution 
                (activity_id, user_id, layer_type, entity_id, auto_allocated_km, action_type)
            VALUES 
                (p_activity_id, p_user_id, 'region', v_zone.region_id, p_total_km, 'defend')
            ON CONFLICT (activity_id, layer_type, entity_id) DO NOTHING;
        END IF;
        
        -- País
        IF v_zone.country_id IS NOT NULL THEN
            INSERT INTO activity_layer_distribution 
                (activity_id, user_id, layer_type, entity_id, auto_allocated_km, action_type)
            VALUES 
                (p_activity_id, p_user_id, 'country', v_zone.country_id, p_total_km, 'defend')
            ON CONFLICT (activity_id, layer_type, entity_id) DO NOTHING;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- VISTAS PARA MAPAS MULTI-ESCALA
-- ==========================================

-- Vista de hexágonos nacionales (baja resolución)
CREATE VIEW v_country_hexagons AS
SELECT 
    ge.id as country_id,
    ge.name as country_name,
    ge.flag_emoji,
    unnest(ge.h3_indexes) as h3_index,
    ge.h3_resolution,
    ge.total_km,
    ge.color
FROM geographic_entities ge
WHERE ge.entity_type = 'country';

-- Vista de batallas en fronteras
CREATE VIEW v_active_border_battles AS
SELECT 
    bz.*,
    ge1.name as entity_1_name,
    ge1.flag_emoji as entity_1_flag,
    ge2.name as entity_2_name,
    ge2.flag_emoji as entity_2_flag,
    array_length(bz.contested_h3_indexes, 1) as contested_zones_count
FROM border_zones bz
JOIN geographic_entities ge1 ON bz.entity_1_id = ge1.id
JOIN geographic_entities ge2 ON bz.entity_2_id = ge2.id
WHERE bz.is_active = TRUE
ORDER BY bz.last_battle_at DESC;

-- Vista de zonas más disputadas
CREATE VIEW v_hottest_battlegrounds AS
SELECT 
    ehc.h3_index,
    ehc.h3_resolution,
    COUNT(DISTINCT ehc.entity_id) as claiming_entities,
    SUM(ehc.control_strength) as total_strength,
    array_agg(DISTINCT ge.name) as entity_names,
    MAX(ehc.last_activity_at) as last_battle
FROM entity_hexagon_control ehc
JOIN geographic_entities ge ON ehc.entity_id = ge.id
WHERE ehc.is_contested = TRUE
GROUP BY ehc.h3_index, ehc.h3_resolution
HAVING COUNT(DISTINCT ehc.entity_id) > 1
ORDER BY SUM(ehc.control_strength) DESC;

-- ==========================================
-- DATOS INICIALES CON HEXÁGONOS
-- ==========================================

-- Ejemplo: Dividir España en hexágonos H3 (resolución 3 para países)
-- En producción, esto se haría con script Python usando h3-py

-- Actualizar España con hexágonos (ejemplo simplificado)
UPDATE geographic_entities 
SET 
    h3_resolution = 3,
    h3_indexes = ARRAY[
        '83754ffffffffff',
        '83755ffffffffff',
        '83756ffffffffff'
        -- ... más hexágonos que cubren España
    ]
WHERE name = 'España' AND entity_type = 'country';

-- Crear fronteras iniciales
INSERT INTO border_zones (entity_1_id, entity_2_id, border_type, contested_h3_indexes) 
SELECT 
    (SELECT id FROM geographic_entities WHERE name = 'España' AND entity_type = 'country'),
    (SELECT id FROM geographic_entities WHERE name = 'Francia' AND entity_type = 'country'),
    'country',
    ARRAY[
        '8375affffffffff',
        '8375bffffffffff'
        -- Hexágonos en la frontera Pirineos
    ];

-- Barcelona vs Madrid
INSERT INTO border_zones (entity_1_id, entity_2_id, border_type, contested_h3_indexes)
SELECT 
    (SELECT id FROM geographic_entities WHERE name = 'Barcelona' AND entity_type = 'city'),
    (SELECT id FROM geographic_entities WHERE name = 'Madrid' AND entity_type = 'city'),
    'city',
    ARRAY[]::TEXT[]; -- No frontera física, pero rivalidad virtual