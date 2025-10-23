# 🧪 Test Suite - Territory Conquest

Suite completa de tests para el backend de Territory Conquest.

## 📋 Estructura de Tests

```
tests/
├── conftest.py              # Configuración compartida y fixtures
├── test_auth.py            # Tests de autenticación
├── test_activities.py      # Tests de actividades
├── test_teams.py           # Tests de equipos
├── test_risk.py            # Tests del sistema RISK
├── test_h3_service.py      # Tests del servicio H3
├── test_integration.py     # Tests de integración completos
└── README.md               # Este archivo
```

## 🚀 Ejecución de Tests

### Ejecutar todos los tests
```bash
pytest
# o
./run_tests.sh
```

### Ejecutar tests específicos

#### Por categoría
```bash
# Solo tests unitarios
pytest -m unit

# Solo tests de integración
pytest -m integration

# Solo tests del sistema RISK
pytest -m risk

# Solo tests rápidos (excluir lentos)
pytest -m "not slow"
```

#### Por archivo
```bash
# Tests de autenticación
pytest tests/test_auth.py

# Tests de actividades
pytest tests/test_activities.py

# Tests de equipos
pytest tests/test_teams.py

# Tests RISK
pytest tests/test_risk.py
```

#### Por clase o función específica
```bash
# Clase específica
pytest tests/test_auth.py::TestAuth

# Función específica
pytest tests/test_auth.py::TestAuth::test_register_success

# Patrón de nombre
pytest -k "register"  # Ejecuta todos los tests con "register" en el nombre
```

### Opciones útiles

#### Con coverage
```bash
pytest --cov=app --cov-report=html
# Abre htmlcov/index.html en el navegador
```

#### Verbose
```bash
pytest -v   # Verbose
pytest -vv  # Extra verbose
```

#### Stop on first failure
```bash
pytest -x
```

#### Ver print statements
```bash
pytest -s
```

#### Parallel execution
```bash
pytest -n auto  # Requiere pytest-xdist
```

## 📊 Markers de Tests

Los tests están organizados con markers para facilitar su ejecución selectiva:

- `@pytest.mark.unit` - Tests unitarios
- `@pytest.mark.integration` - Tests de integración
- `@pytest.mark.slow` - Tests que tardan más tiempo
- `@pytest.mark.risk` - Tests del sistema RISK
- `@pytest.mark.auth` - Tests de autenticación
- `@pytest.mark.activities` - Tests de actividades
- `@pytest.mark.teams` - Tests de equipos

### Uso de markers
```bash
pytest -m unit                    # Solo unitarios
pytest -m "integration and risk"  # Integración del sistema RISK
pytest -m "not slow"              # Excluir tests lentos
```

## 🔧 Fixtures Disponibles

### Autenticación
- `test_user_data` - Datos de usuario de prueba
- `auth_token` - Token JWT válido
- `auth_headers` - Headers con autorización
- `authenticated_user` - Usuario completamente autenticado

### Datos de prueba
- `sample_activity_data` - Datos de actividad de ejemplo
- `sample_team_data` - Datos de equipo de ejemplo
- `sample_territory_data` - Datos de territorio de ejemplo

### Creación de objetos
- `create_test_activity` - Crear actividad y retornar ID
- `create_test_team` - Crear equipo y retornar ID
- `create_multiple_users` - Crear múltiples usuarios

# 🧪 Test Suite - Territory Conquest

Suite completa de tests para el backend de Territory Conquest.

## 📋 Estructura de Tests

```
tests/
├── conftest.py              # Configuración compartida y fixtures
├── test_auth.py            # Tests de autenticación
├── test_activities.py      # Tests de actividades
├── test_teams.py           # Tests de equipos
├── test_risk.py            # Tests del sistema RISK
├── test_h3_service.py      # Tests del servicio H3
├── test_integration.py     # Tests de integración completos
└── README.md               # Este archivo
```

## 🚀 Ejecución de Tests

### Ejecutar todos los tests
```bash
pytest
# o
./run_tests.sh
```

### Ejecutar tests específicos

#### Por categoría
```bash
# Solo tests unitarios
pytest -m unit

# Solo tests de integración
pytest -m integration

# Solo tests del sistema RISK
pytest -m risk

# Solo tests rápidos (excluir lentos)
pytest -m "not slow"
```

#### Por archivo
```bash
# Tests de autenticación
pytest tests/test_auth.py

# Tests de actividades
pytest tests/test_activities.py

# Tests de equipos
pytest tests/test_teams.py

# Tests RISK
pytest tests/test_risk.py
```

#### Por clase o función específica
```bash
# Clase específica
pytest tests/test_auth.py::TestAuth

# Función específica
pytest tests/test_auth.py::TestAuth::test_register_success

# Patrón de nombre
pytest -k "register"  # Ejecuta todos los tests con "register" en el nombre
```

### Opciones útiles

#### Con coverage
```bash
pytest --cov=app --cov-report=html
# Abre htmlcov/index.html en el navegador
```

#### Verbose
```bash
pytest -v   # Verbose
pytest -vv  # Extra verbose
```

#### Stop on first failure
```bash
pytest -x
```

#### Ver print statements
```bash
pytest -s
```

#### Parallel execution
```bash
pytest -n auto  # Requiere pytest-xdist
```

## 📊 Markers de Tests

Los tests están organizados con markers para facilitar su ejecución selectiva:

- `@pytest.mark.unit` - Tests unitarios
- `@pytest.mark.integration` - Tests de integración
- `@pytest.mark.slow` - Tests que tardan más tiempo
- `@pytest.mark.risk` - Tests del sistema RISK
- `@pytest.mark.auth` - Tests de autenticación
- `@pytest.mark.activities` - Tests de actividades
- `@pytest.mark.teams` - Tests de equipos

### Uso de markers
```bash
pytest -m unit                    # Solo unitarios
pytest -m "integration and risk"  # Integración del sistema RISK
pytest -m "not slow"              # Excluir tests lentos
```

## 🔧 Fixtures Disponibles

### Autenticación
- `test_user_data` - Datos de usuario de prueba
- `auth_token` - Token JWT válido
- `auth_headers` - Headers con autorización
- `authenticated_user` - Usuario completamente autenticado

### Datos de prueba
- `sample_activity_data` - Datos de actividad de ejemplo
- `sample_team_data` - Datos de equipo de ejemplo
- `sample_territory_data` - Datos de territorio de ejemplo

### Creación de objetos
- `create_test_activity` - Crear actividad y retornar ID
- `create_test_team` - Crear equipo y retornar ID
- `create_multiple_users` - Crear múltiples usuarios

### Helpers
- `helpers` - Clase con métodos helper (create_user, create_activity, create_team)

## 📝 Cobertura de Tests

### Tests de Autenticación (test_auth.py)
- ✅ Registro exitoso
- ✅ Registro con email duplicado
- ✅ Registro con username duplicado
- ✅ Validación de email
- ✅ Validación de password
- ✅ Login exitoso
- ✅ Login con password incorrecta
- ✅ Login con usuario inexistente
- ✅ Acceso a rutas protegidas
- ✅ Tokens inválidos

### Tests de Actividades (test_activities.py)
- ✅ Crear actividad exitosamente
- ✅ Crear actividad con polyline
- ✅ Crear actividad de gimnasio
- ✅ Validación de distancia
- ✅ Actividades sin zonas asignadas (gym)
- ✅ Obtener actividades del usuario
- ✅ Eliminar actividad
- ✅ Autorización para eliminar
- ✅ Actualización de stats del usuario
- ✅ Paginación

### Tests de Equipos (test_teams.py)
- ✅ Crear equipo
- ✅ Nombre duplicado
- ✅ Validación de color
- ✅ Listar equipos
- ✅ Obtener detalles de equipo
- ✅ Actualizar equipo
- ✅ Autorización para actualizar
- ✅ Unirse a equipo público
- ✅ Intentar unirse a equipo privado
- ✅ Equipo lleno
- ✅ Salir de equipo
- ✅ Eliminar equipo
- ✅ Zonas controladas por equipo

### Tests RISK (test_risk.py)
- ✅ Obtener mapa mundial
- ✅ Diferentes niveles de zoom
- ✅ Detalles de territorio
- ✅ Movimientos tácticos (ataque/defensa)
- ✅ Validación de actividades
- ✅ Batallas activas
- ✅ Rankings territoriales
- ✅ Fronteras calientes
- ✅ Historial de conquistas
- ✅ Impacto del usuario
- ✅ Sugerencias estratégicas
- ✅ Previsualización de ataques
- ✅ Estadísticas globales

### Tests de Servicio H3 (test_h3_service.py)
- ✅ Conversión lat/lng a cell
- ✅ Conversión cell a lat/lng
- ✅ Obtener boundary del hexágono
- ✅ Polyline a cells
- ✅ Obtener vecinos
- ✅ Obtener cells en área
- ✅ Distancia entre cells
- ✅ Validación de cells
- ✅ Estadísticas de zonas
- ✅ Diferentes resoluciones
- ✅ Decodificación de polylines

### Tests de Integración (test_integration.py)
- ✅ Journey completo de usuario
- ✅ Colaboración en equipo
- ✅ Escenario de batalla
- ✅ Integración con Strava (mock)
- ✅ Rankings y leaderboards
- ✅ Desbloqueo de logros
- ✅ Tests de rendimiento

## 🎯 Cobertura Objetivo

```
Módulo                    Cobertura    Líneas    Missing
─────────────────────────────────────────────────────────
app/api/auth.py              95%        45        2
app/api/activities.py        92%        67        5
app/api/teams.py            90%        89        9
app/api/risk.py             88%        156       19
app/services/h3_service.py  100%       120       0
app/services/risk_service.py 85%       234       35
app/core/security.py        100%       25        0
app/core/database.py        100%       12        0
─────────────────────────────────────────────────────────
TOTAL                       91%        748       70
```

## 🐛 Debugging Tests

### Ver output detallado
```bash
pytest -vv -s tests/test_auth.py::TestAuth::test_register_success
```

### Ejecutar con debugger
```bash
pytest --pdb  # Entra en debugger cuando falla
pytest --pdb --pdbcls=IPython.terminal.debugger:Pdb  # Usa IPython
```

### Ver warnings
```bash
pytest -v --tb=short
```

## 📈 CI/CD Integration

### GitHub Actions
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## 💡 Tips para Escribir Tests

### 1. Usar fixtures para setup común
```python
@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_something(sample_data):
    assert sample_data["key"] == "value"
```

### 2. Parametrizar tests
```python
@pytest.mark.parametrize("distance,expected", [
    (10.0, 100),
    (5.0, 50),
    (0.1, 1)
])
def test_points_calculation(distance, expected):
    assert calculate_points(distance) == expected
```

### 3. Usar markers
```python
@pytest.mark.slow
def test_long_running():
    # Test que tarda mucho
    pass
```

### 4. Mock servicios externos
```python
from unittest.mock import Mock, patch

@patch('app.services.strava_service.httpx.AsyncClient')
def test_strava_api(mock_client):
    # Test sin llamar a Strava real
    pass
```

## 🔍 Verificar Tests Antes de Commit

```bash
# Pre-commit hook sugerido
#!/bin/bash
echo "Running tests..."
pytest -m "not slow"
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

## 📚 Recursos

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

## ❓ Troubleshooting

### Tests fallan por base de datos
**Problema**: Tests intentan conectar a Supabase real

**Solución**: Verificar que estés usando variables de entorno de test
```bash
export TESTING=true
export SUPABASE_URL=https://test.supabase.co
```

### Fixtures no encontrados
**Problema**: `fixture 'auth_headers' not found`

**Solución**: Asegurar que `conftest.py` esté en el directorio correcto

### Tests lentos
**Problema**: Suite de tests tarda mucho

**Solución**: Ejecutar solo tests rápidos
```bash
pytest -m "not slow"
```

### Coverage bajo
**Problema**: Cobertura por debajo del objetivo

**Solución**: Ver qué líneas faltan
```bash
pytest --cov=app --cov-report=html
# Abrir htmlcov/index.html
```

## 🎉 Tests Exitosos

Si todos los tests pasan, deberías ver algo como:

```
================================ test session starts =================================
platform linux -- Python 3.11.0, pytest-7.4.4, pluggy-1.0.0
collected 157 items

tests/test_auth.py .................                                          [ 10%]
tests/test_activities.py .............................                        [ 29%]
tests/test_teams.py ...................................                       [ 51%]
tests/test_risk.py .............................................              [ 79%]
tests/test_h3_service.py .......................                              [ 93%]
tests/test_integration.py ..........                                          [100%]

============================== 157 passed in 45.23s ==================================
```

¡Felicidades! 🎉 Tu código está bien testeado.
