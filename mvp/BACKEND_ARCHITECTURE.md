# 🏗️ Backend Architecture - Territory Conquest

## Estructura del Proyecto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app + middleware
│   │
│   ├── core/                      # Configuración central
│   │   ├── __init__.py
│   │   ├── config.py              # Settings & env vars
│   │   ├── security.py            # JWT, passwords, tokens
│   │   ├── exceptions.py          # Custom exceptions
│   │   ├── logging.py             # Structured logging
│   │   └── database.py            # Supabase client
│   │
│   ├── api/                       # API endpoints
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependencies (auth, pagination)
│   │   ├── auth.py                # Auth endpoints
│   │   ├── users.py               # User endpoints
│   │   ├── activities.py          # Activity endpoints
│   │   ├── teams.py               # Team endpoints
│   │   ├── zones.py               # Map/Zone endpoints
│   │   ├── leaderboard.py         # Leaderboard endpoints
│   │   └── stats.py               # Stats endpoints
│   │
│   ├── schemas/                   # Pydantic models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── auth.py
│   │   ├── activity.py
│   │   ├── team.py
│   │   ├── zone.py
│   │   ├── leaderboard.py
│   │   └── common.py              # Shared schemas
│   │
│   ├── services/                  # Business logic
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── activity_service.py
│   │   ├── team_service.py
│   │   ├── zone_service.py
│   │   ├── h3_service.py          # H3 hexagon processing
│   │   ├── points_service.py      # Points calculation
│   │   └── notification_service.py
│   │
│   ├── middleware/                # Custom middleware
│   │   ├── __init__.py
│   │   ├── rate_limit.py          # Rate limiting
│   │   ├── error_handler.py       # Global error handling
│   │   ├── logging_middleware.py  # Request logging
│   │   └── cors.py                # CORS configuration
│   │
│   └── utils/                     # Utilities
│       ├── __init__.py
│       ├── validators.py          # Custom validators
│       ├── geocoding.py           # Lat/lng → City
│       └── helpers.py             # Helper functions
│
├── tests/                         # Tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_activities.py
│   ├── test_teams.py
│   └── test_integration.py
│
├── alembic/                       # DB migrations (optional)
│   ├── versions/
│   └── env.py
│
├── scripts/                       # Utility scripts
│   ├── seed_data.py               # Populate test data
│   └── check_health.py            # Health check script
│
├── .env.example                   # Example environment variables
├── .env                           # Actual env vars (gitignored)
├── .gitignore
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
├── pyproject.toml                 # Project config
├── Dockerfile                     # Docker container
├── docker-compose.yml             # Local dev environment
└── README.md                      # Setup instructions
```

---

## 🎯 Principios de Diseño

### 1. **Separation of Concerns**
- **API Layer** (api/): Solo routing y validación de entrada
- **Service Layer** (services/): Toda la lógica de negocio
- **Data Layer** (database.py): Acceso a datos vía Supabase

### 2. **Dependency Injection**
- Usar FastAPI's `Depends()` para inyectar dependencias
- Facilita testing y reutilización
- Ejemplos: auth, pagination, rate limiting

### 3. **Error Handling Centralizado**
- Custom exceptions en `core/exceptions.py`
- Global error handler en middleware
- Respuestas de error consistentes

### 4. **Type Safety**
- Pydantic schemas para validación
- Type hints en todo el código
- Validación automática de FastAPI

### 5. **Async All The Way**
- Uso de `async/await` en todas las funciones I/O
- Non-blocking operations
- Mejor performance bajo carga

---

## 📦 Tecnologías y Librerías

### Core
```python
fastapi==0.109.0              # Web framework
uvicorn[standard]==0.27.0     # ASGI server
pydantic==2.5.3               # Data validation
pydantic-settings==2.1.0      # Settings management
```

### Database
```python
supabase==2.3.0               # Supabase client
asyncpg==0.29.0               # Async PostgreSQL (optional)
```

### Security
```python
python-jose[cryptography]==3.3.0  # JWT
passlib[bcrypt]==1.7.4            # Password hashing
python-multipart==0.0.6           # Form data
```

### Monitoring & Logging
```python
sentry-sdk==1.39.2            # Error tracking
structlog==23.2.0             # Structured logging
python-json-logger==2.0.7     # JSON logging
```

### Rate Limiting & Caching
```python
slowapi==0.1.9                # Rate limiting
redis==5.0.1                  # Caching (optional)
```

### Testing
```python
pytest==7.4.3                 # Testing framework
pytest-asyncio==0.21.1        # Async tests
httpx==0.25.2                 # Async HTTP client for tests
faker==20.1.0                 # Test data generation
```

### Utilities
```python
h3==3.7.6                     # H3 hexagons
geopy==2.4.1                  # Geocoding
python-dotenv==1.0.0          # Environment variables
```

### Optional
```python
celery==5.3.4                 # Background tasks
flower==2.0.1                 # Celery monitoring
```

---

## 🔧 Configuración por Entorno

### Development (.env.dev)
```bash
# App
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=debug

# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-dev-key
SUPABASE_SERVICE_KEY=your-service-key

# Security
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]

# Rate Limiting
RATE_LIMIT_ENABLED=false

# External Services
SENTRY_DSN=
REDIS_URL=redis://localhost:6379
```

### Production (.env.prod)
```bash
# App
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-prod-key
SUPABASE_SERVICE_KEY=your-prod-service-key

# Security
SECRET_KEY=super-secret-production-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["https://territoryconquest.com"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# External Services
SENTRY_DSN=https://xxx@sentry.io/xxx
REDIS_URL=redis://production-redis:6379

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

---

## 🔐 Capas de Seguridad

### 1. Authentication Layer
```python
# JWT Token validation
# User session management
# Refresh token rotation
# Token blacklisting (Redis)
```

### 2. Authorization Layer
```python
# Role-based access control (RBAC)
# Resource ownership validation
# Team membership checks
```

### 3. Input Validation Layer
```python
# Pydantic schemas
# Custom validators
# SQL injection prevention
# XSS prevention
```

### 4. Rate Limiting Layer
```python
# Per-endpoint limits
# Per-user limits
# IP-based limits
# Gradual backoff
```

### 5. Monitoring Layer
```python
# Sentry for errors
# Structured logging
# Request tracing
# Performance metrics
```

---

## 📊 Database Schema (Supabase)

### Tables (from MVP_SCHEMA_SIMPLIFIED.sql)
```
users                 # User profiles
teams                 # Teams
activities            # Exercise activities
zones                 # H3 hexagon zones
zone_activities       # Activities per zone
control_history       # Zone control changes
```

### Views
```
v_leaderboard_users   # Top users by points
v_leaderboard_teams   # Top teams by points
v_zone_control        # Zone control summary
```

### Functions
```sql
update_user_stats()   # Trigger on activity insert
update_team_stats()   # Trigger on activity insert
update_team_members() # Trigger on user team change
```

---

## 🚀 API Design Patterns

### 1. RESTful Conventions
```
GET    /api/resource          # List
POST   /api/resource          # Create
GET    /api/resource/{id}     # Read
PUT    /api/resource/{id}     # Update
DELETE /api/resource/{id}     # Delete
```

### 2. Response Format
```json
{
  "success": true,
  "data": { ... },
  "message": "Success message",
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100
  }
}
```

### 3. Error Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  },
  "timestamp": "2025-10-23T10:30:00Z"
}
```

### 4. Pagination
```
GET /api/resource?page=1&limit=20&sort=created_at&order=desc
```

### 5. Filtering
```
GET /api/activities?user_id=xxx&date_from=2025-01-01&date_to=2025-12-31
```

---

## 🔄 Request Flow

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Middleware Stack                       │
│  1. CORS                                │
│  2. Request Logging                     │
│  3. Rate Limiting                       │
│  4. Error Handler                       │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  API Router (FastAPI)                   │
│  - Route matching                       │
│  - Request validation (Pydantic)        │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Dependencies                           │
│  - Authentication (get_current_user)    │
│  - Pagination (PaginationParams)        │
│  - Database (get_db)                    │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Service Layer                          │
│  - Business logic                       │
│  - Data processing                      │
│  - External API calls                   │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Database Layer                         │
│  - Supabase queries                     │
│  - Data transformation                  │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────┐
│  Response   │
└─────────────┘
```

---

## 🧪 Testing Strategy

### 1. Unit Tests
```python
# Test individual services
# Mock database calls
# Fast execution
```

### 2. Integration Tests
```python
# Test API endpoints
# Real database (test instance)
# Full request/response cycle
```

### 3. Performance Tests
```python
# Load testing with locust
# Response time monitoring
# Memory profiling
```

### 4. Security Tests
```python
# SQL injection attempts
# XSS attempts
# Authentication bypass
# Rate limiting validation
```

---

## 📈 Performance Optimizations

### 1. Database
- Connection pooling
- Query optimization
- Indexes on foreign keys
- Materialized views for leaderboards

### 2. Caching (Redis)
- User sessions
- Leaderboard data (5 min TTL)
- Zone data (15 min TTL)
- API responses (selective)

### 3. Async Processing
- Background tasks for heavy operations
- Celery for zone processing
- Webhook handlers

### 4. Response Optimization
- Gzip compression
- Response caching headers
- Pagination for large datasets
- Field selection (sparse fieldsets)

---

## 🔍 Monitoring & Observability

### 1. Logging
```python
# Structured JSON logs
# Request ID tracing
# Performance metrics
# Error tracking
```

### 2. Metrics (Prometheus)
```python
# Request count
# Response time
# Error rate
# Active users
```

### 3. Tracing (Sentry)
```python
# Error tracking
# Performance monitoring
# Release tracking
# User feedback
```

### 4. Health Checks
```python
GET /health          # Basic health
GET /health/db       # Database health
GET /health/ready    # Readiness probe
GET /health/live     # Liveness probe
```

---

## 🚀 Deployment

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Render.com
```yaml
# render.yaml
services:
  - type: web
    name: territory-conquest-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ENVIRONMENT
        value: production
```

---

## 📚 Próximos Archivos

He creado la arquitectura completa. Los siguientes archivos contendrán:

1. **BACKEND_IMPLEMENTATION.md** - Código completo de cada módulo
2. **BACKEND_BEST_PRACTICES.md** - Mejores prácticas aplicadas
3. **BACKEND_API_DOCS.md** - Documentación completa de endpoints
4. **BACKEND_TESTING.md** - Tests y ejemplos de uso

¿Continúo con la implementación completa de cada módulo?
