
# 🚀 MVP API - Territory Conquest (Simplified)

## Endpoints Esenciales para MVP

### 📱 **FASE 1: Core Features (4 semanas)**

---

## 1️⃣ AUTENTICACIÓN

### POST /api/auth/register
```json
Request:
{
  "email": "user@example.com",
  "username": "runner123",
  "password": "SecurePass123"
}

Response: 201
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "runner123",
    "email": "user@example.com"
  }
}
```

### POST /api/auth/login
```json
Request:
{
  "email": "user@example.com",
  "password": "SecurePass123"
}

Response: 200
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

---

## 2️⃣ PERFIL USUARIO

### GET /api/users/me
```json
Response: 200
{
  "id": "uuid",
  "username": "runner123",
  "email": "user@example.com",
  "avatar_url": null,
  "total_km": 45.5,
  "total_points": 455,
  "zones_count": 12,
  "team_id": "uuid",
  "rank": 23
}
```

### PUT /api/users/me
```json
Request:
{
  "avatar_url": "https://...",
  "team_id": "uuid"
}
```

---

## 3️⃣ ACTIVIDADES

### POST /api/activities
```json
Request:
{
  "distance_km": 10.5,
  "duration_minutes": 52,
  "lat": 41.3851,
  "lng": 2.1734,
  "recorded_at": "2025-10-23T10:30:00Z"
}

Response: 201
{
  "id": "uuid",
  "distance_km": 10.5,
  "points_earned": 105,
  "zones_affected": [
    {
      "zone_id": "uuid",
      "h3_index": "891f1d...",
      "control_changed": true,
      "new_controller": "Team Red"
    }
  ]
}
```

### GET /api/activities/me?limit=20&offset=0
```json
Response: 200
{
  "total": 45,
  "activities": [
    {
      "id": "uuid",
      "distance_km": 10.5,
      "duration_minutes": 52,
      "points_earned": 105,
      "recorded_at": "2025-10-23T10:30:00Z",
      "city": "Barcelona"
    }
  ]
}
```

---

## 4️⃣ EQUIPOS

### POST /api/teams
```json
Request:
{
  "name": "Barcelona Runners",
  "color": "#FF5733"
}

Response: 201
{
  "id": "uuid",
  "name": "Barcelona Runners",
  "color": "#FF5733",
  "members_count": 1,
  "total_km": 0,
  "total_points": 0
}
```

### GET /api/teams?limit=20
```json
Response: 200
{
  "total": 15,
  "teams": [
    {
      "id": "uuid",
      "name": "Barcelona Runners",
      "color": "#FF5733",
      "members_count": 45,
      "total_km": 1234.5,
      "total_points": 12345,
      "rank": 1
    }
  ]
}
```

### POST /api/teams/{team_id}/join
```json
Response: 200
{
  "message": "Successfully joined team",
  "team": {
    "id": "uuid",
    "name": "Barcelona Runners"
  }
}
```

### GET /api/teams/{team_id}
```json
Response: 200
{
  "id": "uuid",
  "name": "Barcelona Runners",
  "color": "#FF5733",
  "members_count": 45,
  "total_km": 1234.5,
  "total_points": 12345,
  "rank": 1,
  "members": [
    {
      "id": "uuid",
      "username": "runner123",
      "total_km": 45.5,
      "avatar_url": "..."
    }
  ]
}
```

---

## 5️⃣ MAPA (Simplified)

### GET /api/map/zones?city=Barcelona
```json
Response: 200
{
  "city": "Barcelona",
  "total_zones": 234,
  "zones": [
    {
      "id": "uuid",
      "h3_index": "891f1d...",
      "center_lat": 41.3851,
      "center_lng": 2.1734,
      "controlled_by": {
        "team_id": "uuid",
        "team_name": "Barcelona Runners",
        "team_color": "#FF5733"
      },
      "control_strength": 45.5,
      "total_km": 67.8
    }
  ]
}
```

### GET /api/map/boundaries/{h3_index}
```json
Response: 200
{
  "h3_index": "891f1d...",
  "boundary": [
    {"lat": 41.385, "lng": 2.173},
    {"lat": 41.386, "lng": 2.174},
    // ... 6 vertices total
  ]
}
```

---

## 6️⃣ RANKINGS

### GET /api/leaderboard/users?limit=10
```json
Response: 200
{
  "total": 10,
  "leaderboard": [
    {
      "rank": 1,
      "id": "uuid",
      "username": "runner123",
      "avatar_url": "...",
      "total_km": 234.5,
      "total_points": 2345,
      "zones_count": 45,
      "team": {
        "id": "uuid",
        "name": "Barcelona Runners",
        "color": "#FF5733"
      }
    }
  ]
}
```

### GET /api/leaderboard/teams?limit=10
```json
Response: 200
{
  "total": 10,
  "leaderboard": [
    {
      "rank": 1,
      "id": "uuid",
      "name": "Barcelona Runners",
      "color": "#FF5733",
      "total_km": 1234.5,
      "total_points": 12345,
      "members_count": 45,
      "zones_count": 89
    }
  ]
}
```

---

## 7️⃣ STATS

### GET /api/stats/city/{city_name}
```json
Response: 200
{
  "city": "Barcelona",
  "total_users": 234,
  "total_teams": 45,
  "total_km": 12345.6,
  "zones_total": 567,
  "zones_controlled": {
    "Team Red": 234,
    "Team Blue": 189,
    "Neutral": 144
  },
  "top_team": {
    "name": "Barcelona Runners",
    "zones": 234
  }
}
```

---

## 🚫 ELIMINAR DEL MVP

❌ /api/risk/* (todo el sistema RISK complejo)
❌ /api/competitions/* (competiciones)
❌ /api/integrations/* (Strava)
❌ /api/users/{id}/achievements (logros)
❌ Sistema de batallas
❌ Movimientos tácticos
❌ Predicciones
❌ Fronteras calientes

---

## 📊 Prioridad de Implementación

### Semana 1-2: Core Backend
1. Auth (registro/login) ✅
2. Users (perfil básico) ✅
3. Activities (crear/listar) ✅
4. Procesar zonas H3 simple

### Semana 3: Social
5. Teams (crear/unirse) ✅
6. Leaderboards básicos ✅

### Semana 4: Mapa
7. Visualización zonas
8. Control de territorio simple
9. Stats por ciudad

---

## 🎯 Métricas de Éxito del MVP

1. **30 usuarios activos** en primera semana
2. **200+ actividades** registradas
3. **5+ equipos** creados
4. **Engagement**: Usuarios regresan al día siguiente
5. **Feedback**: 80% entiende el concepto de "conquista"

Si estas métricas se cumplen → Continuar con Fase 2
Si no → Pivotar o simplificar más
