# 🎮 Ejemplo de Uso Completo - Sistema RISK

## 📱 Historia de Usuario: Juan en Barcelona

### Día 1: Registro e Inicio

#### 1. Juan se registra
```bash
POST /api/auth/register
{
  "email": "juan@example.com",
  "username": "runner_bcn",
  "password": "SecurePass123",
  "full_name": "Juan García"
}

# Respuesta:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

#### 2. Ve el mapa mundial
```bash
GET /api/risk/map?zoom=world

# Respuesta:
{
  "zoom_level": "world",
  "territories": [
    {
      "id": "uuid-espana",
      "name": "España",
      "controller": {
        "name": "España",
        "flag": "🇪🇸",
        "color": "#AA151B"
      },
      "units": 1567,  // 156,700 km totales
      "is_under_attack": true,
      "battle_progress": 45,
      "icon": "⚔️"
    },
    {
      "id": "uuid-francia",
      "name": "Francia",
      "controller": {
        "name": "Francia",
        "flag": "🇫🇷",
        "color": "#0055A4"
      },
      "units": 1842,
      "is_under_attack": false,
      "icon": ""
    }
  ]
}
```

#### 3. Hace zoom en España
```bash
GET /api/risk/map?zoom=country

# Respuesta muestra regiones:
{
  "territories": [
    {
      "name": "Cataluña",
      "units": 456,
      "is_under_attack": true,
      "icon": "⚔️",
      "battle_progress": 58  // Francia ganando!
    },
    {
      "name": "Madrid",
      "units": 378,
      "is_under_attack": false
    },
    ...
  ]
}
```

---

### Día 2: Primera Actividad

#### 4. Juan corre 10 km en Barcelona
```bash
POST /api/activities
{
  "activity_type": "run",
  "distance_km": 10.0,
  "duration_minutes": 50,
  "polyline": "encoded_polyline...",
  "start_lat": 41.3851,
  "start_lng": 2.1734,
  "recorded_at": "2025-10-01T08:00:00Z"
}

# Respuesta:
{
  "id": "activity-uuid",
  "distance_km": 10.0,
  "points_earned": 100,
  "affected_zones": [
    {"h3_index": "...", "distance_km": 1.2},
    {"h3_index": "...", "distance_km": 0.8},
    ...
  ]
}
```

#### 5. Backend automáticamente DEFIENDE sus territorios
```sql
-- Automático en el backend:
INSERT INTO activity_layer_distribution (activity_id, layer_type, entity_id, auto_allocated_km, action_type)
VALUES 
  ('activity-uuid', 'country', 'uuid-espana', 10.0, 'defend'),
  ('activity-uuid', 'region', 'uuid-catalunya', 10.0, 'defend'),
  ('activity-uuid', 'city', 'uuid-barcelona', 10.0, 'defend');

-- Actualizar unidades:
UPDATE territory_control 
SET units = units + 1  -- 10km / 100 = 0.1 ≈ 1 unidad
WHERE territory_id IN ('uuid-espana', 'uuid-catalunya', 'uuid-barcelona');
```

#### 6. Juan ve las sugerencias estratégicas
```bash
GET /api/risk/user/suggestions

# Respuesta:
{
  "suggestions": [
    {
      "type": "defend_border",
      "priority": "CRITICAL",
      "target": {
        "name": "Frontera Pirineos",
        "entity_1": "España",
        "entity_2": "Francia",
        "spain_control": 42,
        "france_control": 58
      },
      "reason": "Francia ganando frontera (+8% hoy)",
      "recommended_units": 15
    },
    {
      "type": "attack_rival",
      "priority": "MEDIUM",
      "target": {
        "name": "Madrid",
        "units": 378
      },
      "reason": "Rivalidad Barcelona-Madrid (igualados)",
      "recommended_units": 10
    }
  ]
}
```

#### 7. Juan decide ATACAR la frontera francesa
```bash
# Primero, previsualizar
GET /api/risk/preview/battle/uuid-frontera-pirineos?units=10

# Respuesta:
{
  "territory_name": "Frontera Pirineos",
  "current_units": 142,
  "attack_units": 10,
  "success_probability": 12.5,
  "estimated_hexagons_conquered": 2,
  "progress_to_conquest": 8.3,
  "recommendation": "AVOID"  // Muy pocas unidades
}

# Juan decide usar TODAS sus unidades (10)
POST /api/risk/move
{
  "activity_id": "activity-uuid",
  "move_type": "attack",
  "to_territory_id": "uuid-frontera-pirineos",
  "units": 10,
  "km": 10.0
}

# Respuesta:
{
  "move_id": "move-uuid",
  "success": true,
  "conquest_happened": false,
  "was_critical": true,  // Movimiento en batalla crítica
  "units_deployed": 10
}
```

---

### Día 3: Ver Impacto

#### 8. Juan ve su impacto
```bash
GET /api/risk/user/impact

# Respuesta:
{
  "total_moves": 1,
  "critical_moves": 1,
  "conquests_participated": 0,
  "territories_impacted": 4,  // España, Cataluña, Barcelona, Frontera
  "total_units_deployed": 11,  // 1 defensa + 10 ataque
  "total_km_allocated": 20.0,
  "average_impact_per_move": 11.0
}
```

#### 9. Ver estado de la batalla
```bash
GET /api/risk/battles

# Respuesta:
{
  "total": 3,
  "battles": [
    {
      "id": "battle-uuid",
      "territory_name": "Cataluña",
      "defender_name": "España",
      "defender_flag": "🇪🇸",
      "defender_units": 456,
      "attacker_name": "Francia",
      "attacker_flag": "🇫🇷",
      "attacker_units": 512,
      "conquest_progress": 55.8,
      "threat_level": "🟠 PELIGRO",
      "days_fighting": 12
    }
  ]
}
```

#### 10. Ver detalle de la batalla
```bash
GET /api/risk/battles/battle-uuid

# Respuesta:
{
  "battle": {...},
  "recent_moves": [
    {
      "user": {
        "username": "runner_bcn",
        "avatar_url": "..."
      },
      "units_moved": 10,
      "km_allocated": 10.0,
      "created_at": "2025-10-01T08:15:00Z",
      "was_critical": true
    },
    {
      "user": {
        "username": "coureur_fr",
        "avatar_url": "..."
      },
      "units_moved": 15,
      "km_allocated": 15.0,
      "created_at": "2025-10-01T07:30:00Z"
    }
  ],
  "hexagon_map": [
    {
      "h3_index": "8975abc...",
      "controller": "team-azul",
      "strength": 45.2,
      "contested_by": "team-rojo",
      "recent_activity": 12.5
    }
  ]
}
```

---

### Semana 1: Estrategia Avanzada

#### 11. Juan crea un equipo
```bash
POST /api/teams
{
  "name": "Barcelona Runners",
  "description": "Conquistando España kilómetro a kilómetro",
  "color": "#004D98",
  "is_public": true
}
```

#### 12. Amigos se unen
```bash
POST /api/teams/{team_id}/join
```

#### 13. Coordinar ataque masivo
```
Domingo 10:00 - Plan de ataque:
- 5 miembros corren simultáneamente
- Todos atacan Frontera Pirineos
- Total: 50 unidades (500 km)

POST /api/risk/move (x5 usuarios)
```

#### 14. Ver resultado
```bash
GET /api/risk/history/conquests

# Respuesta:
{
  "conquests": [
    {
      "territory_name": "Frontera Pirineos (Sector Este)",
      "previous_controller": "Francia 🇫🇷",
      "new_controller": "España 🇪🇸",
      "decisive_user": "runner_bcn",
      "battle_duration_days": 14,
      "conquered_at": "2025-10-07T11:23:45Z"
    }
  ]
}
```

---

### Mes 1: Dominio Regional

#### 15. Ver ranking territorial
```bash
GET /api/risk/rankings?scope=country

# Respuesta:
{
  "rankings": [
    {
      "controller_name": "España",
      "controller_flag": "🇪🇸",
      "territories_controlled": 45,
      "total_units": 2145,
      "capitals_controlled": 8,
      "fortresses_controlled": 12,
      "territories_under_attack": 3
    },
    {
      "controller_name": "Francia",
      "controller_flag": "🇫🇷",
      "territories_controlled": 52,
      "total_units":
