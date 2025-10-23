-- SCHEMA PARA SISTEMA RISK
-- Añadir después de enhanced_multi_layer_schema.sql

-- ==========================================
-- TERRITORIOS RISK
-- ==========================================
ALTER TABLE geographic_entities ADD COLUMN territory_type VARCHAR(50) DEFAULT 'standard';
-- Tipos: standard, fortress, strategic_point, border, neutral

ALTER TABLE geographic_entities ADD COLUMN defense_bonus DECIMAL(5, 2) DEFAULT 0;
-- Bonus de defensa (0 = normal, 0.5 = +50%, 1.0 = +100%)

ALTER TABLE geographic_entities ADD COLUMN units INTEGER DEFAULT 0;
-- "Ejército" visible en el mapa (total_km / 100)

ALTER TABLE geographic_entities ADD COLUMN production_rate INTEGER DEFAULT 0;
-- Unidades que produce automáticamente por día

ALTER TABLE geographic_entities ADD COLUMN is_capital BOOLEAN DEFAULT FALSE;
-- Si es capital de región/país

ALTER TABLE geographic_entities ADD COLUMN connected_territories UUID[];
-- Array de IDs de territorios conectados (para bonus de cadena)

-- ==========================================
-- CONTROL Y CONQUISTA
-- ==========================================
CREATE TABLE territory_control (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    territory_id UUID NOT NULL REFERENCES geographic_entities(id),
    
    -- Control actual
    controlling_entity VARCHAR(50) NOT NULL, -- country, team, user
    controller_id UUID, -- ID del controlador
    controller_name VARCHAR(255), -- España, Equipo Azul, etc
    controller_flag VARCHAR(10), -- 🇪🇸
    controller_color VARCHAR(7), -- #FF0000
    
    -- Fuerza militar (unidades)
    units INTEGER DEFAULT 0,
    total_km DECIMAL(12, 2) DEFAULT 0,
    
    -- Tiempo de control
    controlled_since TIMESTAMPTZ DEFAULT NOW(),
    days_controlled INTEGER DEFAULT 0,
    
    -- Estado
    is_under_attack BOOLEAN DEFAULT FALSE,
    attack_strength INTEGER DEFAULT 0, -- Unidades atacantes
    
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(territory_id)
);

CREATE INDEX idx_territory_control_controller ON territory_control(controller_id);
CREATE INDEX idx_territory_control_attack ON territory_control(is_under_attack) WHERE is_under_attack = TRUE;

-- ==========================================
-- BATALLAS EN CURSO
-- ==========================================
CREATE TABLE active_battles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Territorio en disputa
    territory_id UUID NOT NULL REFERENCES geographic_entities(id),
    territory_name VARCHAR(255),
    
    -- Defensor
    defender_entity VARCHAR(50), -- country, team, user
    defender_id UUID,
    defender_name VARCHAR(255),
    defender_flag VARCHAR(10),
    defender_units INTEGER,
    
    -- Atacante principal
    attacker_entity VARCHAR(50),
    attacker_id UUID,
    attacker_name VARCHAR(255),
    attacker_flag VARCHAR(10),
    attacker_units INTEGER,
    
    -- Stats de batalla
    total_hexagons INTEGER, -- Hexágonos totales en territorio
    defender_hexagons INTEGER, -- Hexágonos controlados por defensor
    attacker_hexagons INTEGER, -- Hexágonos controlados por atacante
    contested_hexagons INTEGER, -- Hexágonos en disputa activa
    
    -- Estado
    battle_status VARCHAR(50) DEFAULT 'ongoing', -- ongoing, defender_winning, attacker_winning
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Resultado potencial
    conquest_progress DECIMAL(5, 2) DEFAULT 0, -- % hacia conquista (70% = victoria)
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_battles_territory ON active_battles(territory_id);
CREATE INDEX idx_battles_status ON active_battles(battle_status);
CREATE INDEX idx_battles_activity ON active_battles(last_activity_at DESC);

-- ==========================================
-- MOVIMIENTOS TÁCTICOS
-- ==========================================
CREATE TABLE tactical_moves (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Usuario que hace el movimiento
    user_id UUID NOT NULL REFERENCES users(id),
    activity_id UUID NOT NULL REFERENCES activities(id),
    
    -- Acción
    move_type VARCHAR(50) NOT NULL, -- attack, defend, reinforce, transfer
    
    -- Origen y destino
    from_territory_id UUID REFERENCES geographic_entities(id),
    to_territory_id UUID NOT NULL REFERENCES geographic_entities(id),
    
    -- Recursos
    units_moved INTEGER NOT NULL,
    km_allocated DECIMAL(10, 2) NOT NULL,
    
    -- Resultado
    success BOOLEAN,
    hexagons_conquered INTEGER DEFAULT 0,
    impact_score INTEGER, -- Puntuación de impacto del movimiento
    
    -- Contexto
    was_critical BOOLEAN DEFAULT FALSE, -- Movimiento crítico en batalla
    turned_tide BOOLEAN DEFAULT FALSE, -- Cambió el curso de la batalla
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_moves_user ON tactical_moves(user_id);
CREATE INDEX idx_moves_territory ON tactical_moves(to_territory_id);
CREATE INDEX idx_moves_critical ON tactical_moves(was_critical) WHERE was_critical = TRUE;

-- ==========================================
-- HISTORIAL DE CONQUISTAS
-- ==========================================
CREATE TABLE conquest_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    territory_id UUID NOT NULL REFERENCES geographic_entities(id),
    territory_name VARCHAR(255),
    
    -- Cambio de control
    previous_controller VARCHAR(255),
    previous_flag VARCHAR(10),
    new_controller VARCHAR(255),
    new_flag VARCHAR(10),
    
    -- Batalla que llevó a la conquista
    battle_id UUID REFERENCES active_battles(id),
    decisive_move_id UUID REFERENCES tactical_moves(id),
    decisive_user_id UUID REFERENCES users(id),
    
    -- Stats
    battle_duration_days INTEGER,
    total_participants INTEGER,
    units_exchanged INTEGER,
    
    conquered_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conquest_territory ON conquest_history(territory_id);
CREATE INDEX idx_conquest_date ON conquest_history(conquered_at DESC);

-- ==========================================
-- CONTINENTAL CONTROL (Bonus RISK)
-- ==========================================
CREATE TABLE continental_bonuses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    continent_name VARCHAR(100) NOT NULL UNIQUE,
    total_territories INTEGER NOT NULL,
    bonus_units_per_day INTEGER NOT NULL,
    
    -- Control actual
    controlled_by_entity VARCHAR(50),
    controlled_by_id UUID,
    controlled_by_name VARCHAR(255),
    territories_controlled INTEGER DEFAULT 0,
    control_percentage DECIMAL(5, 2) DEFAULT 0,
    
    -- Última conquista total
    last_full_control_at TIMESTAMPTZ,
    last_full_controller VARCHAR(255),
    
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Datos iniciales continentes
INSERT INTO continental_bonuses (continent_name, total_territories, bonus_units_per_day) VALUES
('Europe', 42, 5),
('Asia', 67, 7),
('North America', 38, 5),
('South America', 28, 2),
('Africa', 45, 3),
('Oceania', 12, 2);

-- ==========================================
-- FUNCIONES AUTOMÁTICAS
-- ==========================================

-- Calcular unidades desde KM totales
CREATE OR REPLACE FUNCTION calculate_units_from_km()
RETURNS TRIGGER AS $$
BEGIN
    NEW.units = FLOOR(NEW.total_km / 100);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_calc_units BEFORE INSERT OR UPDATE ON geographic_entities
FOR EACH ROW EXECUTE FUNCTION calculate_units_from_km();

-- Detectar batallas automáticamente
CREATE OR REPLACE FUNCTION detect_battle(p_territory_id UUID)
RETURNS void AS $$
DECLARE
    v_control RECORD;
    v_attackers RECORD;
    v_total_hex INTEGER;
    v_defender_hex INTEGER;
    v_attacker_hex INTEGER;
BEGIN
    -- Obtener control actual
    SELECT * INTO v_control FROM territory_control WHERE territory_id = p_territory_id;
    
    IF NOT FOUND THEN RETURN; END IF;
    
    -- Contar hexágonos por controlador
    SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE controlling_team = v_control.controller_id) as defender,
        COUNT(*) FILTER (WHERE controlling_team != v_control.controller_id AND controlling_team IS NOT NULL) as attacker
    INTO v_total_hex, v_defender_hex, v_attacker_hex
    FROM zones
    WHERE city_id = p_territory_id OR region_id = p_territory_id OR country_id = p_territory_id;
    
    -- Si hay atacantes significativos (>20%), crear/actualizar batalla
    IF v_attacker_hex::DECIMAL / v_total_hex > 0.2 THEN
        INSERT INTO active_battles (
            territory_id,
            territory_name,
            defender_entity,
            defender_id,
            defender_name,
            defender_units,
            total_hexagons,
            defender_hexagons,
            attacker_hexagons,
            conquest_progress
        )
        SELECT
            p_territory_id,
            (SELECT name FROM geographic_entities WHERE id = p_territory_id),
            v_control.controlling_entity,
            v_control.controller_id,
            v_control.controller_name,
            v_control.units,
            v_total_hex,
            v_defender_hex,
            v_attacker_hex,
            (v_attacker_hex::DECIMAL / v_total_hex) * 100
        ON CONFLICT (territory_id) DO UPDATE SET
            defender_hexagons = EXCLUDED.defender_hexagons,
            attacker_hexagons = EXCLUDED.attacker_hexagons,
            conquest_progress = EXCLUDED.conquest_progress,
            last_activity_at = NOW(),
            battle_status = CASE
                WHEN EXCLUDED.conquest_progress > 70 THEN 'attacker_winning'
                WHEN EXCLUDED.conquest_progress < 30 THEN 'defender_winning'
                ELSE 'ongoing'
            END;
        
        -- Marcar territorio como bajo ataque
        UPDATE territory_control 
        SET is_under_attack = TRUE, attack_strength = v_attacker_hex
        WHERE territory_id = p_territory_id;
    ELSE
        -- No hay batalla, limpiar
        DELETE FROM active_battles WHERE territory_id = p_territory_id;
        UPDATE territory_control 
        SET is_under_attack = FALSE, attack_strength = 0
        WHERE territory_id = p_territory_id;
    END IF;
END;
$ LANGUAGE plpgsql;

-- Verificar conquista de territorio
CREATE OR REPLACE FUNCTION check_conquest(p_territory_id UUID, p_attacker_id UUID)
RETURNS BOOLEAN AS $
DECLARE
    v_total_hex INTEGER;
    v_attacker_hex INTEGER;
    v_conquest_pct DECIMAL;
    v_battle RECORD;
    v_defender RECORD;
BEGIN
    -- Obtener batalla y defensor
    SELECT * INTO v_battle FROM active_battles WHERE territory_id = p_territory_id;
    SELECT * INTO v_defender FROM territory_control WHERE territory_id = p_territory_id;
    
    IF NOT FOUND THEN RETURN FALSE; END IF;
    
    -- Calcular control del atacante
    v_conquest_pct := (v_battle.attacker_hexagons::DECIMAL / v_battle.total_hexagons) * 100;
    
    -- Si controla >70% → CONQUISTA
    IF v_conquest_pct >= 70 THEN
        -- Registrar conquista
        INSERT INTO conquest_history (
            territory_id,
            territory_name,
            previous_controller,
            previous_flag,
            new_controller,
            battle_id,
            battle_duration_days,
            units_exchanged
        ) VALUES (
            p_territory_id,
            v_battle.territory_name,
            v_defender.controller_name,
            v_defender.controller_flag,
            v_battle.attacker_name,
            v_battle.id,
            EXTRACT(DAY FROM NOW() - v_battle.started_at),
            v_battle.attacker_units + v_battle.defender_units
        );
        
        -- Cambiar control
        UPDATE territory_control SET
            controller_id = p_attacker_id,
            controller_name = v_battle.attacker_name,
            controller_flag = v_battle.attacker_flag,
            units = v_battle.attacker_units,
            controlled_since = NOW(),
            days_controlled = 0,
            is_under_attack = FALSE
        WHERE territory_id = p_territory_id;
        
        -- Cerrar batalla
        UPDATE active_battles SET battle_status = 'conquered' WHERE id = v_battle.id;
        DELETE FROM active_battles WHERE id = v_battle.id;
        
        RETURN TRUE;
    END IF;
    
    RETURN FALSE;
END;
$ LANGUAGE plpgsql;

-- Incrementar días de control automáticamente (ejecutar diariamente)
CREATE OR REPLACE FUNCTION increment_control_days()
RETURNS void AS $
BEGIN
    UPDATE territory_control
    SET 
        days_controlled = days_controlled + 1,
        units = units + (SELECT production_rate FROM geographic_entities WHERE id = territory_id)
    WHERE NOT is_under_attack;
END;
$ LANGUAGE plpgsql;

-- ==========================================
-- VISTAS PARA VISUALIZACIÓN RISK
-- ==========================================

-- Vista de mapa mundial (territorios con su estado)
CREATE VIEW v_risk_world_map AS
SELECT 
    ge.id as territory_id,
    ge.name as territory_name,
    ge.entity_type as territory_type,
    ge.center_lat,
    ge.center_lng,
    ge.h3_indexes,
    ge.territory_type as special_type,
    ge.defense_bonus,
    ge.is_capital,
    tc.controller_name,
    tc.controller_flag,
    tc.controller_color,
    tc.units,
    tc.is_under_attack,
    tc.days_controlled,
    COALESCE(ab.conquest_progress, 0) as battle_progress,
    CASE 
        WHEN tc.is_under_attack THEN '⚔️'
        WHEN ge.is_capital THEN '⭐'
        WHEN ge.territory_type = 'fortress' THEN '🏰'
        WHEN ge.territory_type = 'strategic_point' THEN '🎯'
        ELSE ''
    END as icon
FROM geographic_entities ge
LEFT JOIN territory_control tc ON ge.id = tc.territory_id
LEFT JOIN active_battles ab ON ge.id = ab.territory_id
WHERE ge.entity_type IN ('city', 'region', 'country');

-- Vista de batallas activas con detalles
CREATE VIEW v_active_battles_detail AS
SELECT 
    ab.*,
    ge.name as territory_display_name,
    ge.territory_type,
    (ab.attacker_hexagons::DECIMAL / ab.total_hexagons * 100) as attacker_control_pct,
    (ab.defender_hexagons::DECIMAL / ab.total_hexagons * 100) as defender_control_pct,
    EXTRACT(DAY FROM NOW() - ab.started_at) as days_fighting,
    CASE 
        WHEN ab.conquest_progress > 70 THEN '🔴 CRÍTICO'
        WHEN ab.conquest_progress > 50 THEN '🟠 PELIGRO'
        WHEN ab.conquest_progress > 30 THEN '🟡 ALERTA'
        ELSE '🟢 CONTROLADO'
    END as threat_level
FROM active_battles ab
JOIN geographic_entities ge ON ab.territory_id = ge.id
WHERE ab.battle_status = 'ongoing'
ORDER BY ab.conquest_progress DESC;

-- Vista de rankings territoriales
CREATE VIEW v_territorial_rankings AS
SELECT 
    tc.controller_name,
    tc.controller_flag,
    tc.controller_color,
    COUNT(*) as territories_controlled,
    SUM(tc.units) as total_units,
    SUM(tc.total_km) as total_km,
    COUNT(*) FILTER (WHERE ge.is_capital) as capitals_controlled,
    COUNT(*) FILTER (WHERE ge.territory_type = 'fortress') as fortresses_controlled,
    COUNT(*) FILTER (WHERE tc.is_under_attack) as territories_under_attack,
    AVG(tc.days_controlled) as avg_days_controlled
FROM territory_control tc
JOIN geographic_entities ge ON tc.territory_id = ge.id
GROUP BY tc.controller_name, tc.controller_flag, tc.controller_color
ORDER BY territories_controlled DESC, total_units DESC;

-- Vista de fronteras calientes
CREATE VIEW v_hot_borders AS
SELECT 
    bz.id,
    ge1.name as entity_1_name,
    ge1.flag_emoji as entity_1_flag,
    ge2.name as entity_2_name,
    ge2.flag_emoji as entity_2_flag,
    bz.entity_1_control_pct,
    bz.entity_2_control_pct,
    bz.total_battles,
    bz.last_battle_at,
    array_length(bz.contested_h3_indexes, 1) as contested_hexagons,
    CASE 
        WHEN ABS(bz.entity_1_control_pct - 50) < 10 THEN '🔥 MUY DISPUTADA'
        WHEN ABS(bz.entity_1_control_pct - 50) < 25 THEN '⚔️ ACTIVA'
        ELSE '🛡️ ESTABLE'
    END as border_status
FROM border_zones bz
JOIN geographic_entities ge1 ON bz.entity_1_id = ge1.id
JOIN geographic_entities ge2 ON bz.entity_2_id = ge2.id
WHERE bz.is_active = TRUE
ORDER BY 
    ABS(bz.entity_1_control_pct - 50) ASC,
    bz.total_battles DESC;

-- ==========================================
-- PROCEDIMIENTO PARA REGISTRAR MOVIMIENTO TÁCTICO
-- ==========================================
CREATE OR REPLACE FUNCTION register_tactical_move(
    p_user_id UUID,
    p_activity_id UUID,
    p_move_type VARCHAR,
    p_from_territory_id UUID,
    p_to_territory_id UUID,
    p_units INTEGER,
    p_km DECIMAL
)
RETURNS JSONB AS $
DECLARE
    v_move_id UUID;
    v_result JSONB;
    v_hexagons_conquered INTEGER := 0;
    v_was_critical BOOLEAN := FALSE;
    v_turned_tide BOOLEAN := FALSE;
    v_conquest_happened BOOLEAN := FALSE;
BEGIN
    -- Crear movimiento
    INSERT INTO tactical_moves (
        user_id, activity_id, move_type,
        from_territory_id, to_territory_id,
        units_moved, km_allocated
    ) VALUES (
        p_user_id, p_activity_id, p_move_type,
        p_from_territory_id, p_to_territory_id,
        p_units, p_km
    ) RETURNING id INTO v_move_id;
    
    -- Actualizar territorio destino
    UPDATE territory_control
    SET 
        units = units + p_units,
        total_km = total_km + p_km,
        updated_at = NOW()
    WHERE territory_id = p_to_territory_id;
    
    -- Si es ataque, detectar batalla
    IF p_move_type = 'attack' THEN
        PERFORM detect_battle(p_to_territory_id);
        
        -- Verificar si hubo conquista
        v_conquest_happened := check_conquest(p_to_territory_id, p_user_id);
        
        -- Determinar criticidad
        SELECT is_under_attack, attack_strength
        INTO v_was_critical
        FROM territory_control
        WHERE territory_id = p_to_territory_id;
    END IF;
    
    -- Actualizar movimiento con resultado
    UPDATE tactical_moves SET
        success = TRUE,
        hexagons_conquered = v_hexagons_conquered,
        was_critical = v_was_critical,
        turned_tide = v_turned_tide
    WHERE id = v_move_id;
    
    -- Construir respuesta
    v_result := jsonb_build_object(
        'move_id', v_move_id,
        'success', TRUE,
        'conquest_happened', v_conquest_happened,
        'was_critical', v_was_critical,
        'units_deployed', p_units
    );
    
    RETURN v_result;
END;
$ LANGUAGE plpgsql;

-- ==========================================
-- DATOS INICIALES
-- ==========================================

-- Crear control inicial para España
INSERT INTO territory_control (territory_id, controlling_entity, controller_name, controller_flag, controller_color, units)
SELECT 
    id,
    'country',
    name,
    flag_emoji,
    color,
    FLOOR(total_km / 100)
FROM geographic_entities
WHERE entity_type IN ('country', 'region', 'city')
ON CONFLICT DO NOTHING;

-- Marcar fortalezas (ciudades grandes)
UPDATE geographic_entities SET
    territory_type = 'fortress',
    defense_bonus = 0.5,
    production_rate = 3,
    is_capital = TRUE
WHERE name IN ('Barcelona', 'Madrid', 'Valencia', 'Sevilla', 'Bilbao')
AND entity_type = 'city';

-- Marcar puntos estratégicos
UPDATE geographic_entities SET
    territory_type = 'strategic_point',
    defense_bonus = 0.3
WHERE name LIKE '%Pirineos%' OR name LIKE '%Frontera%';