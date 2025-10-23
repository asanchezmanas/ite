# 📋 Plan de Implementación MVP - Territory Conquest

## 🎯 Objetivo del MVP

**Validar la hipótesis central**: ¿Los usuarios quieren "conquistar territorio" haciendo ejercicio?

**NO validar**: Sistema RISK complejo, batallas, competiciones, integraciones.

---

## 📅 Roadmap de Implementación

### **FASE 1: MVP Core (4 semanas) - PRIORITARIO**

#### Semana 1: Foundation
- [x] Setup básico FastAPI + Supabase
- [ ] Schema simplificado (6 tablas)
- [ ] Auth (registro/login/JWT)
- [ ] Tests básicos de auth
- [ ] Deploy en Render

**Entregable**: Backend con auth funcionando

#### Semana 2: Activities & Zones
- [ ] Endpoint POST /activities
- [ ] Servicio H3 simplificado (solo 1 resolución)
- [ ] Procesar zonas de una actividad
- [ ] Cálculo básico de control (team con más KM)
- [ ] Tests de actividades

**Entregable**: Registrar actividad actualiza zonas

#### Semana 3: Social Features
- [ ] CRUD de Teams
- [ ] Unirse/salir de team
- [ ] Leaderboard usuarios (top 10)
- [ ] Leaderboard equipos (top 5)
- [ ] Tests de teams

**Entregable**: Sistema de equipos funcional

#### Semana 4: Map Visualization Prep
- [ ] Endpoint GET /map/zones
- [ ] Endpoint GET /map/boundaries
- [ ] Stats por ciudad
- [ ] Optimizar queries pesadas
- [ ] Documentation API completa

**Entregable**: API lista para frontend

---

### **FASE 2: Frontend Básico (3 semanas)**

#### Semana 5: Setup & Auth
- [ ] Setup React/Vue/Next.js
- [ ] Páginas login/registro
- [ ] Dashboard básico
- [ ] Integrar API auth

#### Semana 6: Core Features
- [ ] Formulario nueva actividad
- [ ] Lista de actividades
- [ ] Ver mi perfil
- [ ] Ver teams
- [ ] Unirse a team

#### Semana 7: Mapa Básico
- [ ] Integrar mapa (Mapbox/Leaflet)
- [ ] Renderizar hexágonos H3
- [ ] Colores por equipo
- [ ] Leaderboards
- [ ] PWA básica

**Entregable**: MVP completo para beta testers

---

### **FASE 3: Beta Testing (2 semanas)**

#### Semana 8: Testing Interno
- [ ] Invitar 10 beta testers
- [ ] Recoger feedback
- [ ] Fix bugs críticos
- [ ] Ajustes UX

#### Semana 9: Lanzamiento Soft
- [ ] Invitar 30 usuarios más
- [ ] Monitorear métricas
- [ ] Iterar según feedback

**Entregable**: MVP validado o pivotado

---

### **FASE 4: Post-MVP (según validación)**

Solo implementar si Fase 3 es exitosa:

- [ ] Integración Strava
- [ ] Sistema de logros
- [ ] Competiciones simples
- [ ] Notificaciones push
- [ ] Versión móvil nativa

---

## 🔥 Cambios Críticos vs. Tu Código Actual

### 1. **Simplificar Schema**

**ANTES (20+ tablas)**:
```sql
- geographic_entities
- competitions
- activity_allocations
- border_zones
- strategic_attacks
- territory_control
- active_battles
- tactical_moves
- conquest_history
- continental_bonuses
- entity_hexagon_control
- activity_layer_distribution
```

**AHORA (6 tablas)**:
```sql
users
teams
activities
zones
zone_activities
control_history
```

### 2. **Eliminar Endpoints Complejos**

**ELIMINAR**:
```python
# app/api/risk.py (TODO)
- /api/risk/map (multi-escala)
- /api/risk/territory/{id}
- /api/risk/move (movimientos tácticos)
- /api/risk/battles
- /api/risk/preview/battle
- /api/risk/rankings
- /api/risk/borders/hot
- /api/risk/history/conquests
- /api/risk/user/impact
- /api/risk/user/suggestions

# app/api/competitions.py (TODO)
- Todo el módulo de competiciones

# app/api/integrations.py (TODO)
- Integración Strava (Fase 4)
```

**MANTENER Y SIMPLIFICAR**:
```python
# app/api/activities.py
POST /api/activities (simplificado)
GET /api/activities/me

# app/api/teams.py
POST /api/teams
GET /api/teams
POST /api/teams/{id}/join

# app/api/zones.py (nuevo, simple)
GET /api/map/zones?city=Barcelona

# app/api/leaderboard.py
GET /api/leaderboard/users
GET /api/leaderboard/teams
```

### 3. **Simplificar Procesamiento H3**

**ANTES**:
```python
# Procesar polyline completo
# Múltiples resoluciones
# Recalcular en tiempo real
# Distribución multi-capa
```

**AHORA**:
```python
def process_activity_simple(lat, lng, distance_km):
    """
    1. Obtener zona H3 del punto inicial
    2. Añadir KM a esa zona
    3. Actualizar control si supera threshold (5km)
    4. FIN - Todo async en background
    """
    h3_index = h3.latlng_to_cell(lat, lng, 9)
    
    # Add to zone
    zone = get_or_create_zone(h3_index)
    zone.add_km(distance_km, team_id)
    
    # Check control (solo si pasa threshold)
    if zone.team_km >= CONTROL_THRESHOLD:
        zone.update_control()
```

### 4. **Eliminar Features Complejas**

**ELIMINAR**:
- ❌ Sistema RISK multi-escala
- ❌ Batallas en tiempo real
- ❌ Predicciones de ataques
- ❌ Fronteras calientes
- ❌ Movimientos tácticos
- ❌ Competiciones
- ❌ Logros complejos

**MANTENER**:
- ✅ Registro de actividades
- ✅ Control de zonas simple
- ✅ Equipos básicos
- ✅ Rankings
- ✅ Visualización mapa

---

## 🎯 Métricas de Éxito

### Semana 4 (Backend Ready)
- [ ] API documentation completa
- [ ] 90%+ tests passing
- [ ] <200ms response time
- [ ] Deploy estable en Render

### Semana 9 (MVP Completo)
- [ ] 30 usuarios activos
- [ ] 200+ actividades registradas
- [ ] 5+ equipos
- [ ] 70%+ usuarios vuelven al día siguiente
- [ ] <5% error rate

### Decisión Go/No-Go
Si métricas se cumplen → Fase 4
Si no → Pivotar o parar

---

## ⚠️ Riesgos y Mitigaciones

### Riesgo 1: Complejidad H3
**Riesgo**: Procesamiento lento de hexágonos
**Mitigación**: 
- Limitar a 1 hexágono por actividad en MVP
- Procesar en background con Celery/Redis
- Cachear boundaries

### Riesgo 2: Escalabilidad BD
**Riesgo**: Queries lentas con muchas zonas
**Mitigación**:
- Índices en todas las columnas críticas
- Paginación en todos los endpoints
- Limitar zonas por ciudad (max 500)

### Riesgo 3: Adopción Usuario
**Riesgo**: Usuarios no entienden "conquista"
**Mitigación**:
- Onboarding claro
- Tutorial interactivo
- Feedback inmediato en UI

### Riesgo 4: Scope Creep
**Riesgo**: Añadir features antes de validar
**Mitigación**:
- Checklist estricto de MVP
- No tocar código post-Fase 1
- Focus en métricas

---

## 💰 Costos Estimados (MVP)

### Desarrollo
- Backend: 4 semanas × $0 (tú)
- Frontend: 3 semanas × $0 (tú)
- **Total Dev: $0**

### Infraestructura
- Supabase Free tier: $0/mes
- Render Free tier: $0/mes
- Mapbox Free: $0/mes (50k requests)
- **Total Infra: $0/mes para MVP**

### Contingencia
- Render Paid ($7/mes) si MVP crece
- Supabase Pro ($25/mes) si >500 usuarios

---

## 📚 Recursos Necesarios

### Backend
- [x] FastAPI
- [x] Supabase
- [x] H3-py
- [ ] Redis (Fase 4)
- [ ] Celery (Fase 4)

### Frontend (Fase 2)
- [ ] React/Next.js
- [ ] Mapbox GL JS
- [ ] TailwindCSS
- [ ] React Query

### DevOps
- [x] GitHub
- [x] Render
- [ ] Sentry (errors)
- [ ] PostHog (analytics)

---

## 🚦 Semáforo de Decisión

### 🟢 VERDE - Continuar (Fase 1 → Fase 2)
- API funcionando
- Tests >80% pass
- Deploy estable

### 🟡 AMARILLO - Revisar
- Tests <80% pass
- Performance issues
- Bugs críticos sin resolver

### 🔴 ROJO - Parar y Replantear
- MVP no se completa en 4 semanas
- Problemas técnicos bloqueantes
- Scope sigue creciendo

---

## ✅ Checklist Pre-Launch

### Backend
- [ ] Schema simplificado implementado
- [ ] 6 endpoints core funcionando
- [ ] Tests >90% coverage
- [ ] API docs publicadas
- [ ] Deploy production estable
- [ ] Monitoreo básico activo

### Antes de Fase 2
- [ ] API validada con Postman
- [ ] Performance aceptable (<500ms)
- [ ] Sin bugs críticos
- [ ] Feedback de 3+ developers

---

## 🎯 Conclusión

**TU CÓDIGO ACTUAL**: Excelente arquitectura pero demasiado ambicioso para MVP (9/10 técnico, 4/10 MVP)

**MVP PROPUESTO**: Enfocado en validación rápida (6/10 técnico, 9/10 MVP)

**Recomendación**: Implementar MVP simplificado primero, añadir complejidad SOLO si se valida.

**Timeline realista**: 
- 4 semanas backend MVP
- 3 semanas frontend básico
- 2 semanas beta testing
- **= 9 semanas para validación**

¿Prefieres validar en 2 meses o construir todo en 6 meses sin saber si funciona? 🚀
