# app/tests/test_auth.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAuth:
    """Tests para autenticación"""
    
    def test_register_success(self):
        """Registro exitoso de usuario"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "SecurePass123",
                "full_name": "Test User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_register_duplicate_email(self):
        """Registro con email duplicado debe fallar"""
        # Primer registro
        client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user1",
                "password": "Pass123"
            }
        )
        
        # Segundo registro con mismo email
        response = client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user2",
                "password": "Pass123"
            }
        )
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_duplicate_username(self):
        """Registro con username duplicado debe fallar"""
        client.post(
            "/api/auth/register",
            json={
                "email": "user1@example.com",
                "username": "sameuser",
                "password": "Pass123"
            }
        )
        
        response = client.post(
            "/api/auth/register",
            json={
                "email": "user2@example.com",
                "username": "sameuser",
                "password": "Pass123"
            }
        )
        
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]
    
    def test_register_invalid_email(self):
        """Registro con email inválido"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "username": "testuser",
                "password": "Pass123"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_register_short_password(self):
        """Registro con password muy corta"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "123"
            }
        )
        
        assert response.status_code == 422
    
    def test_login_success(self):
        """Login exitoso"""
        # Crear usuario
        client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "password": "SecurePass123"
            }
        )
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "SecurePass123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self):
        """Login con password incorrecta"""
        client.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "CorrectPass123"
            }
        )
        
        response = client.post(
            "/api/auth/login",
            json={
                "email": "user@example.com",
                "password": "WrongPass123"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self):
        """Login con usuario que no existe"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Pass123"
            }
        )
        
        assert response.status_code == 401
    
    def test_logout(self):
        """Logout"""
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"


class TestAuthProtectedRoutes:
    """Tests para rutas protegidas"""
    
    @pytest.fixture
    def auth_headers(self):
        """Fixture que retorna headers con token válido"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "protected@example.com",
                "username": "protecteduser",
                "password": "Pass123"
            }
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_access_protected_route_without_token(self):
        """Acceder a ruta protegida sin token"""
        response = client.get("/api/users/me")
        assert response.status_code == 403  # Forbidden
    
    def test_access_protected_route_with_token(self, auth_headers):
        """Acceder a ruta protegida con token válido"""
        response = client.get("/api/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "protected@example.com"
    
    def test_access_protected_route_with_invalid_token(self):
        """Acceder con token inválido"""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/api/users/me", headers=headers)
        assert response.status_code == 401
