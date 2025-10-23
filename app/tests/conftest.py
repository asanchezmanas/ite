# app/tests/conftest.py

"""
Configuración compartida de pytest para todos los tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime


# Cliente de test global
@pytest.fixture(scope="session")
def test_client():
    """Cliente de test para toda la sesión"""
    return TestClient(app)


# Fixtures de autenticación reutilizables
@pytest.fixture
def test_user_data():
    """Datos de usuario de prueba"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPass123",
        "full_name": "Test User"
    }


@pytest.fixture
def register_user(test_client, test_user_data):
    """Registrar usuario de prueba"""
    response = test_client.post("/api/auth/register", json=test_user_data)
    return response.json()


@pytest.fixture
def auth_token(test_client, test_user_data):
    """Token de autenticación"""
    response = test_client.post("/api/auth/register", json=test_user_data)
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Headers con autenticación"""
    return {"Authorization": f"Bearer {auth_token}"}


# Fixtures para datos de prueba
@pytest.fixture
def sample_activity_data():
    """Datos de actividad de ejemplo"""
    return {
        "activity_type": "run",
        "distance_km": 10.0,
        "duration_minutes": 50,
        "start_lat": 41.3851,
        "start_lng": 2.1734,
        "recorded_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_team_data():
    """Datos de equipo de ejemplo"""
    return {
        "name": "Test Team",
        "description": "Team for testing",
        "color": "#FF0000",
        "is_public": True
    }


# Fixtures de limpieza
@pytest.fixture(autouse=True)
def reset_test_data():
    """Limpiar datos de prueba después de cada test"""
    yield
    # Aquí podrías agregar lógica de limpieza si es necesario
    pass


# Fixtures para testing de RISK
@pytest.fixture
def sample_territory_data():
    """Datos de territorio de ejemplo"""
    return {
        "name": "Test Territory",
        "entity_type": "city",
        "center_lat": 41.3851,
        "center_lng": 2.1734
    }


@pytest.fixture
def create_test_activity(test_client, auth_headers, sample_activity_data):
    """Crear actividad de prueba y retornar su ID"""
    response = test_client.post(
        "/api/activities",
        headers=auth_headers,
        json=sample_activity_data
    )
    return response.json()["id"]


@pytest.fixture
def create_test_team(test_client, auth_headers, sample_team_data):
    """Crear equipo de prueba y retornar su ID"""
    response = test_client.post(
        "/api/teams",
        headers=auth_headers,
        json=sample_team_data
    )
    return response.json()["id"]


# Fixtures para múltiples usuarios
@pytest.fixture
def create_multiple_users(test_client):
    """Crear múltiples usuarios de prueba"""
    users = []
    for i in range(3):
        user_data = {
            "email": f"user{i}@example.com",
            "username": f"user{i}",
            "password": "Pass123"
        }
        response = test_client.post("/api/auth/register", json=user_data)
        token = response.json()["access_token"]
        users.append({
            "data": user_data,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        })
    return users


# Helpers de testing
class TestHelpers:
    """Clase con métodos helper para tests"""
    
    @staticmethod
    def create_user(client, email, username, password="Pass123"):
        """Helper para crear usuario"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password
            }
        )
        return response.json()
    
    @staticmethod
    def create_activity(client, headers, distance_km=10.0):
        """Helper para crear actividad"""
        response = client.post(
            "/api/activities",
            headers=headers,
            json={
                "activity_type": "run",
                "distance_km": distance_km,
                "recorded_at": datetime.utcnow().isoformat()
            }
        )
        return response.json()
    
    @staticmethod
    def create_team(client, headers, name="Test Team"):
        """Helper para crear equipo"""
        response = client.post(
            "/api/teams",
            headers=headers,
            json={
                "name": name,
                "color": "#FF0000",
                "is_public": True
            }
        )
        return response.json()


@pytest.fixture
def helpers():
    """Fixture para acceder a helpers"""
    return TestHelpers


# Markers personalizados para organizar tests
def pytest_configure(config):
    """Configuración adicional de pytest"""
    config.addinivalue_line(
        "markers", "slow: marca tests lentos"
    )
    config.addinivalue_line(
        "markers", "integration: tests de integración completos"
    )
    config.addinivalue_line(
        "markers", "unit: tests unitarios aislados"
    )
