# ✅ Checklist Accionable - Territory Conquest MVP

## 🎯 Objetivo
Transformar tu código actual en un MVP validable en 9 semanas.

---

## 📋 FASE 1: Simplificación Backend (Semana 1-2)

### Día 1-2: Decisión y Setup
- [ ] Leer todos los documentos de análisis
- [ ] Decidir: ¿Simplificar o continuar con código actual?
- [ ] Si simplificar: Crear branch `mvp-simplified`
- [ ] Backup de código actual en branch `full-vision`
- [ ] Crear proyecto en Trello/Notion para tracking

### Día 3-5: Database Schema
- [ ] Ejecutar `MVP_SCHEMA_SIMPLIFIED.sql` en Supabase
- [ ] Crear nueva base de datos `territory_conquest_mvp`
- [ ] Verificar que todas las tablas se crearon correctamente
- [ ] Verificar triggers funcionan
- [ ] Verificar views se crearon
- [ ] Popular con datos de prueba mínimos

### Día 6-7: Migrar Models
```python
# Actualizar estos archivos:
- [ ] app/models/user.py (simplificar campos)
- [ ] app/models/team.py (simplificar campos)
- [ ] app/models/activity.py (simplificar, sin polyline por ahora)
- [ ] app/models/zone.py (simplificar)
- [ ] ELIMINAR: app/models/competition.py
- [ ] ELIMINAR: app/models/risk_*.py
```

### Día 8-10: API Endpoints
```python
# MANTENER Y SIMPLIFICAR:
- [ ] app/api/auth.py (ya está bien)
- [ ] app/api/users.py (simplificar)
- [ ] app/api/teams.py (simplificar)
- [ ] app/api/activities.py (simplificar proceso H3)

# ELIMINAR COMPLETAMENTE:
- [ ] app/api/risk.py
- [ ] app/api/competitions.py
- [ ] app/api/integrations.py (guardar para Fase 4)

# CREAR NUEVO:
- [ ] app/api/map.py (simple, solo GET /zones)
```

### Día 11-12: Services
```python
# SIMPLIFICAR:
- [ ] app/services/h3_service.py
      → Solo procesar 1 punto inicial
      → Eliminar polyline processing (Fase 2)

- [ ] app/services/activity_processor.py
      → Simplificar a proceso básico
      → Sin multi-capa distribution

- [ ] app/services/zone_control.py
      → Control simple por threshold
      → Sin recálculo complejo

# ELIMINAR:
- [ ] app/services/risk_service.py
- [ ] app/services/competition_service.py
- [ ] app/services/strava_service.py (guardar para Fase 4)
```

### Día 13-14: Testing
- [ ] Actualizar todos los tests
- [ ] Eliminar tests de features removidas
- [ ] Crear tests para proceso simplificado
- [ ] Ejecutar suite completa: `pytest`
- [ ] Coverage >85%

---

## 📋 FASE 2: Optimización (Semana 3-4)

### Semana 3: Performance

#### Database
- [ ] Añadir indexes faltantes
```sql
CREATE INDEX idx_activities_user_date ON activities(user_id, recorded_at DESC);
CREATE INDEX idx_zones_city_team ON zones(city, controlled_by_team);
CREATE INDEX idx_zone_activities_recorded ON zone_activities(recorded_at DESC);
```

- [ ] Optimizar N+1 queries
- [ ] Crear funciones SQL para queries complejas
- [ ] Materializar views pesadas

#### Code
- [ ] Implementar rate limiting con SlowAPI
```python
pip install slowapi
# En cada endpoint crítico
@limiter.limit("10/minute")
```

- [ ] Error handling estándar
```python
# Crear app/core/exceptions.py
# Implementar global error handler
```

- [ ] Implementar refresh tokens
```python
# En app/core/security.py
# Nuevo endpoint POST /auth/refresh
```

### Semana 4: Production Ready

#### Monitoring
- [ ] Integrar Sentry
```bash
pip install sentry-sdk
# Setup en app/main.py
```

- [ ] Añadir logging estructurado
```python
import structlog
# Setup en app/core/logging.py
```

- [ ] Health check robusto
```python
@app.get("/health")
async def health():
    # Check DB
    # Check Redis (si aplica)
    # Return status
```

#### Documentation
- [ ] API docs con FastAPI Swagger
- [ ] README para developers
- [ ] Postman collection
- [ ] Environment variables documented

#### Deploy
- [ ] Configurar Render.com
- [ ] Variables de entorno production
- [ ] CI/CD básico con GitHub Actions
- [ ] Smoke tests post-deploy

---

## 📋 FASE 3: Frontend MVP (Semana 5-7)

### Semana 5: Setup & Auth

- [ ] Decidir stack frontend (React/Vue/Next.js)
- [ ] Setup proyecto
```bash
npx create-next-app territory-conquest
cd territory-conquest
npm install
```

- [ ] Setup TailwindCSS
- [ ] Setup React Query / SWR
- [ ] Integrar API client

**Páginas a crear:**
- [ ] Landing page simple
- [ ] Login page
- [ ] Register page
- [ ] Dashboard skeleton

### Semana 6: Core Features

**Páginas principales:**
- [ ] Dashboard
  - [ ] Stats del usuario (KM, puntos, ranking)
  - [ ] Últimas actividades
  - [ ] Info del equipo si tiene

- [ ] Nueva Actividad
  - [ ] Formulario simple (distancia + ubicación)
  - [ ] Botón "Usar mi ubicación actual"
  - [ ] Feedback inmediato al registrar

- [ ] Mis Actividades
  - [ ] Lista de actividades
  - [ ] Ver zonas afectadas
  - [ ] Eliminar actividad

- [ ] Equipos
  - [ ] Lista de equipos
  - [ ] Crear equipo
  - [ ] Unirse a equipo
  - [ ] Ver miembros

- [ ] Leaderboards
  - [ ] Top 10 usuarios
  - [ ] Top 5 equipos
  - [ ] Mi posición

### Semana 7: Mapa

- [ ] Integrar Mapbox/Leaflet
```bash
npm install mapbox-gl
# o
npm install react-leaflet
```

- [ ] Renderizar hexágonos H3
```javascript
// Obtener boundaries del backend
// Renderizar polígonos coloreados
// Tooltip con info de zona
```

- [ ] Centrar en ciudad del usuario
- [ ] Zoom controls
- [ ] Click en hexágono → ver detalles

**Features del mapa:**
- [ ] Ver mis zonas (highlight)
- [ ] Ver zonas del equipo (color del equipo)
- [ ] Ver zonas neutrales
- [ ] Leyenda

---

## 📋 FASE 4: Beta Testing (Semana 8-9)

### Semana 8: Testing Interno

- [ ] Invite 10 beta testers
  - [ ] 5 runners activos
  - [ ] 3 ciclistas
  - [ ] 2 walkers

- [ ] Onboarding session
  - [ ] Tutorial del concepto
  - [ ] Demo de features
  - [ ] Dar "misiones" iniciales

- [ ] Recoger feedback estructurado
```
Google Form con:
- ¿Entiendes el concepto? (1-5)
- ¿Usarías esto regularmente? (1-5)
- ¿Qué NO te gusta?
- ¿Qué cambiarías?
- ¿Lo recomendarías?
```

- [ ] Fix bugs críticos diariamente
- [ ] Monitorear métricas
  - Actividades por usuario
  - Retention día siguiente
  - Tiempo en app
  - Crashes / errors

### Semana 9: Lanzamiento Soft

- [ ] Invitar 30 usuarios más
  - Enfocarte en 1-2 ciudades
  - Grupos existentes (running clubs)

- [ ] Marketing mínimo
  - [ ] Post en r/running (si permiten)
  - [ ] Story en Instagram personal
  - [ ] WhatsApp a amigos runners

- [ ] Monitorear métricas diariamente
```
Objetivo Semana 9:
- 30+ usuarios registrados
- 200+ actividades
- 5+ equipos creados
- 60%+ retention día siguiente
```

- [ ] Daily standups (tú solo)
  - ¿Qué funcionó ayer?
  - ¿Qué NO funcionó?
  - ¿Qué cambiar hoy?

---

## 🎯 Métricas de Éxito

### Fin Semana 2 (Backend MVP)
```
✅ 6 tablas en producción
✅ 16 endpoints funcionando
✅ Tests >85% coverage
✅ API docs publicadas
✅ <500ms response time
```

### Fin Semana 4 (Backend Production Ready)
```
✅ Rate limiting activo
✅ Error handling estándar
✅ Monitoring con Sentry
✅ Deploy estable en Render
✅ No critical bugs
```

### Fin Semana 7 (Frontend MVP)
```
✅ 7 páginas funcionando
✅ Mapa con hexágonos
✅ PWA installable
✅ Mobile responsive
✅ <3s load time
```

### Fin Semana 9 (Validación)
```
🎯 30+ usuarios activos
🎯 200+ actividades
🎯 5+ equipos
🎯 60%+ retention
🎯 Feedback mayormente positivo
```

---

## 🚦 Red Flags (Parar y Revisar)

### Durante Desarrollo
- 🔴 Semana 2 no completada → Scope muy grande aún
- 🔴 Tests <70% coverage → Mala calidad
- 🔴 Response time >1s → Problemas performance
- 🔴 Deploy falla constantemente → Config issues

### Durante Testing
- 🔴 <15 usuarios en Semana 8 → No hay interés
- 🔴 <50 actividades en Semana 8 → No engagement
- 🔴 Feedback negativo consistente → Concepto no funciona
- 🔴 Crashes/bugs críticos frecuentes → No production ready

---

## 💡 Tips para Mantenerte Enfocado

### DO ✅
- Trabajar en orden del checklist
- Commit frecuente (daily)
- Tests antes de features
- Pedir feedback temprano
- Celebrar milestones

### DON'T ❌
- Añadir "just one more feature"
- Optimizar antes de medir
- Perfectionism over progress
- Trabajar sin breaks
- Ignorar feedback negativo

---

## 📞 Cuando Pedir Ayuda

- Technical blocker >4 horas → Stack Overflow
- Design decision → Post en r/webdev
- User feedback confuso → Hablar con 3 usuarios
- Burnout → Tomar 1-2 días off

---

## 🎉 Hitos a Celebrar

- [ ] ✅ Semana 2: Backend MVP deployed
- [ ] ✅ Semana 4: First user activity registered
- [ ] ✅ Semana 7: First hexagon conquered
- [ ] ✅ Semana 8: First team formed
- [ ] ✅ Semana 9: 30 users milestone

---

## 📂 Quick Commands

### Development
```bash
# Backend
uvicorn app.main:app --reload

# Tests
pytest -v

# Tests con coverage
pytest --cov=app --cov-report=html

# Deploy
git push origin mvp-simplified
# Render auto-deploys
```

### Frontend (cuando llegues ahí)
```bash
npm run dev
npm run build
npm run test
```

---

## ✅ Daily Checklist Template

### Morning
- [ ] Review yesterday's progress
- [ ] Pick 3 tasks for today
- [ ] Check no critical issues in production

### Afternoon
- [ ] Complete planned tasks
- [ ] Write tests for new code
- [ ] Commit + push

### Evening
- [ ] Update progress tracker
- [ ] Note what blocked me
- [ ] Plan tomorrow's 3 tasks

---

## 🎯 Uso de Este Checklist

1. **Imprime o copia a Notion/Trello**
2. **Marca checkboxes al completar**
3. **No saltes pasos**
4. **Revisa semanalmente**
5. **Ajusta si necesario**

---

## 🚀 EMPEZAR HOY

Tu primer commit del MVP simplificado:

```bash
# 1. Crear branch
git checkout -b mvp-simplified

# 2. Backup código actual
git tag full-vision-backup

# 3. Leer documentos
# - MVP_SCHEMA_SIMPLIFIED.sql
# - MVP_API_SIMPLIFIED.md
# - MVP_IMPLEMENTATION_PLAN.md

# 4. Ejecutar schema en Supabase

# 5. Comenzar simplificación

# 6. Commit frecuente
git commit -m "MVP: Simplified schema implemented"
```

---

**¡A simplificar y validar! 🚀**

Recuerda: Mejor un MVP simple funcionando que un producto complejo sin terminar.
