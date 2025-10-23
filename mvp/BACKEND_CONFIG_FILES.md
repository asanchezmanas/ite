# 📦 Backend - Requirements & Configuration Files

## requirements.txt (Production)

```txt
# ============================================
# Core Framework
# ============================================
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# ============================================
# Database & ORM
# ============================================
supabase==2.3.0
postgrest==0.13.1
realtime==1.0.0
storage3==0.6.1

# ============================================
# Authentication & Security
# ============================================
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.1.2

# ============================================
# Data Validation
# ============================================
pydantic==2.5.3
pydantic-settings==2.1.0
email-validator==2.1.0

# ============================================
# Logging & Monitoring
# ============================================
structlog==23.2.0
python-json-logger==2.0.7
sentry-sdk[fastapi]==1.39.2

# ============================================
# Rate Limiting
# ============================================
slowapi==0.1.9
limits==3.7.0

# ============================================
# HTTP Client (for external APIs)
# ============================================
httpx==0.25.2
aiohttp==3.9.1

# ============================================
# Geospatial
# ============================================
h3==3.7.6
geopy==2.4.1

# ============================================
# Utilities
# ============================================
python-dotenv==1.0.0
python-dateutil==2.8.2
pytz==2023.3

# ============================================
# Optional: Caching (if using Redis)
# ============================================
redis==5.0.1
hiredis==2.3.2

# ============================================
# Optional: Background Tasks
# ============================================
# celery==5.3.4
# flower==2.0.1

# ============================================
# Optional: Better CORS
# ============================================
# fastapi-cors==0.0.6
```

---

## requirements-dev.txt (Development)

```txt
# Include production requirements
-r requirements.txt

# ============================================
# Testing
# ============================================
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
faker==20.1.0
factory-boy==3.3.0

# ============================================
# Code Quality
# ============================================
black==23.12.1
isort==5.13.2
flake8==6.1.0
mypy==1.7.1
pylint==3.0.3
bandit==1.7.5

# ============================================
# Type Stubs
# ============================================
types-python-dateutil==2.8.19
types-pytz==2023.3.1.1

# ============================================
# Development Tools
# ============================================
ipython==8.18.1
ipdb==0.13.13
watchdog==3.0.0

# ============================================
# Documentation
# ============================================
mkdocs==1.5.3
mkdocs-material==9.5.2

# ============================================
# Performance Profiling
# ============================================
py-spy==0.3.14
memory-profiler==0.61.0
```

---

## .env.example

```bash
# ============================================
# Application
# ============================================
APP_NAME=Territory Conquest API
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=debug

# ============================================
# Server
# ============================================
HOST=0.0.0.0
PORT=8000
WORKERS=1

# ============================================
# Database - Supabase
# ============================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here

# ============================================
# Security
# ============================================
SECRET_KEY=your-secret-key-min-32-chars-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ============================================
# CORS
# ============================================
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
CORS_CREDENTIALS=true
CORS_METHODS=["*"]
CORS_HEADERS=["*"]

# ============================================
# Rate Limiting
# ============================================
RATE_LIMIT_ENABLED=false
RATE_LIMIT_PER_MINUTE=60

# ============================================
# Redis (Optional)
# ============================================
REDIS_URL=redis://localhost:6379
REDIS_ENABLED=false

# ============================================
# External Services
# ============================================
SENTRY_DSN=
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=0.1

# ============================================
# Monitoring
# ============================================
ENABLE_METRICS=false
METRICS_PORT=9090

# ============================================
# Business Logic
# ============================================
POINTS_PER_KM=10
ZONE_CONTROL_THRESHOLD_KM=5.0
DEFAULT_CITY=Barcelona
H3_RESOLUTION=9

# ============================================
# Pagination
# ============================================
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
```

---

## .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/
.venv

# Environment Variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# Logs
*.log
logs/

# Database
*.db
*.sqlite

# OS
.DS_Store
Thumbs.db

# Project specific
uploads/
temp/
cache/
```

---

## pyproject.toml

```toml
[tool.poetry]
name = "territory-conquest-api"
version = "1.0.0"
description = "Territory conquest through sports - Backend API"
authors = ["Your Name <your@email.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
supabase = "^2.3.0"
pydantic = "^2.5.3"
pydantic-settings = "^2.1.0"

[tool.poetry.dev-dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
black = "^23.12.1"
isort = "^5.13.2"
mypy = "^1.7.1"

[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --cov=app --cov-report=html --cov-report=term"
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
plugins = ["pydantic.mypy"]

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
```

---

## Dockerfile

```dockerfile
# ============================================
# Multi-stage build for production
# ============================================

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY ./app ./app

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## docker-compose.yml

```yaml
version: '3.8'

services:
  # API Service
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: territory-api
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - LOG_LEVEL=debug
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=redis://redis:6379
      - REDIS_ENABLED=true
    volumes:
      - ./app:/app/app
    depends_on:
      - redis
    restart: unless-stopped
    networks:
      - territory-network

  # Redis (optional - for caching)
  redis:
    image: redis:7-alpine
    container_name: territory-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    networks:
      - territory-network

  # Redis Commander (optional - Redis UI)
  redis-commander:
    image: rediscommander/redis-commander:latest
    container_name: territory-redis-ui
    environment:
      - REDIS_HOSTS=local:redis:6379
    ports:
      - "8081:8081"
    depends_on:
      - redis
    networks:
      - territory-network

volumes:
  redis-data:

networks:
  territory-network:
    driver: bridge
```

---

## render.yaml

```yaml
# Render.com configuration
services:
  # Web service
  - type: web
    name: territory-conquest-api
    env: python
    region: oregon
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
    healthCheckPath: /health
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: false
      - key: LOG_LEVEL
        value: info
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false
      - key: SECRET_KEY
        generateValue: true
      - key: SENTRY_DSN
        sync: false
      - key: CORS_ORIGINS
        value: '["https://territoryconquest.com"]'
      - key: RATE_LIMIT_ENABLED
        value: true
```

---

## .github/workflows/ci.yml

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 app --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Format check with black
      run: |
        black --check app
    
    - name: Import sort check with isort
      run: |
        isort --check-only app
    
    - name: Type check with mypy
      run: |
        mypy app
    
    - name: Test with pytest
      run: |
        pytest --cov=app --cov-report=xml --cov-report=html
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        fail_ci_if_error: true

  security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Bandit security check
      run: |
        pip install bandit
        bandit -r app -ll
```

---

## Makefile

```makefile
.PHONY: help install dev test lint format clean docker

help:
	@echo "Available commands:"
	@echo "  make install  - Install production dependencies"
	@echo "  make dev      - Install dev dependencies and run server"
	@echo "  make test     - Run tests with coverage"
	@echo "  make lint     - Run linters"
	@echo "  make format   - Format code"
	@echo "  make clean    - Clean cache and temp files"
	@echo "  make docker   - Build and run with Docker"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements-dev.txt
	uvicorn app.main:app --reload --port 8000

test:
	pytest --cov=app --cov-report=html --cov-report=term

lint:
	flake8 app
	mypy app
	bandit -r app

format:
	black app
	isort app

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

docker:
	docker-compose up --build
```

---

## 🚀 Quick Start Commands

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env file
cp .env.example .env
# Edit .env with your credentials

# Run migrations (if needed)
# python scripts/migrate.py

# Run server
uvicorn app.main:app --reload --port 8000
```

### Development
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Format code
make format

# Run tests
make test

# Run linters
make lint
```

### Docker
```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop
docker-compose down
```

### Production (Render.com)
```bash
# Push to GitHub
git push origin main

# Render will auto-deploy
# Or manually deploy in Render dashboard
```

---

## ✅ Verification Checklist

- [ ] requirements.txt copied
- [ ] .env.example copied and configured as .env
- [ ] .gitignore copied
- [ ] pyproject.toml copied (if using Poetry)
- [ ] Dockerfile copied (if using Docker)
- [ ] docker-compose.yml copied (if using Docker)
- [ ] render.yaml copied (if deploying to Render)
- [ ] .github/workflows/ci.yml copied (if using GitHub Actions)
- [ ] Makefile copied
- [ ] All commands work
- [ ] Server runs successfully
- [ ] Tests pass (if implemented)
- [ ] Linters pass

---

¡Listo! Tienes todos los archivos de configuración necesarios para un backend profesional. 🚀
