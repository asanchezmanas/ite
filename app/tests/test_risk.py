# app/tests/test_risk.py

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app

client = TestClient(app)


@pytest.fixture
def authenticated_user():
    """Usuario autenticado"""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "conqueror@example.com",
            "username": "conqueror",
            "password": "Pass123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def activity_id(authenticated_user):
    """Crear actividad de prueba"""
    response = client.post(
        "/api/activities",
        headers=authenticated_user,
        json={
            "activity_type": "run",
            "distance_km": 10.0,
            "recorded_at": datetime.utcnow().isoformat()
        }
    )
    return response.json()["id"]


class TestRiskMap:
    """Tests para mapa RISK"""
    
    def test_get_world_map(self):
        """Obtener mapa mundial"""
        response = client.get("/api/risk/map?zoom=world")
        
        assert response.status_code == 200
        data = response.json()
        assert "zoom_level" in data
        assert data["zoom_level"] == "world"
        assert "territories" in data
        assert isinstance(data["territories"], list)
    
    def test_get_country_map(self):
        """Obtener mapa de país (regiones)"""
        response = client.get("/api/risk/map?zoom=country")
        
        assert response.status_code == 200
        data = response.json()
        assert data["zoom_level"] == "country"
    
    def test_get_region_map(self):
        """Obtener mapa regional (ciudades)"""
        response = client.get("/api/risk/map?zoom=region")
        
        assert response.status_code == 200
        data = response.json()
        assert data["zoom_level"] == "region"
    
    def test_get_city_map(self):
        """Obtener mapa de ciudad (distritos)"""
        response = client.get("/api/risk/map?zoom=city")
        
        assert response.status_code == 200
    
    def test_invalid_zoom_level(self):
        """Zoom level inválido"""
        response = client.get("/api/risk/map?zoom=invalid")
        
        assert response.status_code == 422
    
    def test_map_territory_structure(self):
        """Verificar estructura de territorios"""
        response = client.get("/api/risk/map?zoom=world")
        data = response.json()
        
        if data["territories"]:
            territory = data["territories"][0]
            assert "id" in territory
            assert "name" in territory
            assert "controller" in territory
            assert "units" in territory
            assert "is_under_attack" in territory


class TestTerritoryDetails:
    """Tests para detalles de territorios"""
    
    def test_get_territory_detail(self):
        """Obtener detalles de territorio"""
        # Primero obtener un territorio del mapa
        map_response = client.get("/api/risk/map?zoom=world")
        territories = map_response.json()["territories"]
        
        if territories:
            territory_id = territories[0]["id"]
            
            response = client.get(f"/api/risk/territory/{territory_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert "territory" in data
            assert "control" in data
            assert "hexagon_distribution" in data
            assert "connected_territories" in data
            assert "strategic_value" in data
    
    def test_get_nonexistent_territory(self):
        """Obtener territorio que no existe"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/risk/territory/{fake_id}")
        
        assert response.status_code == 404


class TestTacticalMoves:
    """Tests para movimientos tácticos"""
    
    def test_attack_move(self, authenticated_user, activity_id):
        """Ejecutar ataque a territorio"""
        # Obtener un territorio objetivo del mapa
        map_response = client.get("/api/risk/map?zoom=world")
        territories = map_response.json()["territories"]
        
        if territories:
            target_territory = territories[0]["id"]
            
            response = client.post(
                "/api/risk/move",
                headers=authenticated_user,
                json={
                    "activity_id": activity_id,
                    "move_type": "attack",
                    "to_territory_id": target_territory,
                    "units": 10,
                    "km": 10.0
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "move_id" in data
            assert "success" in data
            assert data["success"] is True
    
    def test_defend_move(self, authenticated_user, activity_id):
        """Ejecutar defensa de territorio"""
        map_response = client.get("/api/risk/map?zoom=world")
        territories = map_response.json()["territories"]
        
        if territories:
            target_territory = territories[0]["id"]
            
            response = client.post(
                "/api/risk/move",
                headers=authenticated_user,
                json={
                    "activity_id": activity_id,
                    "move_type": "defend",
                    "to_territory_id": target_territory,
                    "units": 10,
                    "km": 10.0
                }
            )
            
            assert response.status_code == 200
    
    def test_move_with_invalid_activity(self, authenticated_user):
        """Movimiento con actividad inválida"""
        fake_activity_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.post(
            "/api/risk/move",
            headers=authenticated_user,
            json={
                "activity_id": fake_activity_id,
                "move_type": "attack",
                "to_territory_id": "00000000-0000-0000-0000-000000000000",
                "units": 10,
                "km": 10.0
            }
        )
        
        assert response.status_code == 404
    
    def test_move_unauthorized_activity(self, authenticated_user):
        """Intentar usar actividad de otro usuario"""
        # Crear usuario 2 y su actividad
        user2_response = client.post(
            "/api/auth/register",
            json={
                "email": "user2@example.com",
                "username": "user2",
                "password": "Pass123"
            }
        )
        user2_token = {"Authorization": f"Bearer {user2_response.json()['access_token']}"}
        
        activity_response = client.post(
            "/api/activities",
            headers=user2_token,
            json={
                "activity_type": "run",
                "distance_km": 10.0,
                "recorded_at": datetime.utcnow().isoformat()
            }
        )
        user2_activity_id = activity_response.json()["id"]
        
        # Usuario 1 intenta usar actividad de usuario 2
        response = client.post(
            "/api/risk/move",
            headers=authenticated_user,
            json={
                "activity_id": user2_activity_id,
                "move_type": "attack",
                "to_territory_id": "00000000-0000-0000-0000-000000000000",
                "units": 10,
                "km": 10.0
            }
        )
        
        assert response.status_code == 404


class TestBattles:
    """Tests para batallas"""
    
    def test_get_active_battles(self):
        """Obtener batallas activas"""
        response = client.get("/api/risk/battles")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "battles" in data
        assert isinstance(data["battles"], list)
    
    def test_get_user_related_battles(self, authenticated_user):
        """Obtener batallas relacionadas con el usuario"""
        response = client.get(
            "/api/risk/battles?user_related=true",
            headers=authenticated_user
        )
        
        assert response.status_code == 200
    
    def test_get_battle_detail(self):
        """Obtener detalles de batalla"""
        # Primero obtener batallas activas
        battles_response = client.get("/api/risk/battles")
        battles = battles_response.json()["battles"]
        
        if battles:
            battle_id = battles[0]["id"]
            
            response = client.get(f"/api/risk/battles/{battle_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert "battle" in data
            assert "recent_moves" in data
            assert "participants" in data
            assert "hexagon_map" in data


class TestRankings:
    """Tests para rankings territoriales"""
    
    def test_get_global_rankings(self):
        """Obtener rankings globales"""
        response = client.get("/api/risk/rankings?scope=global")
        
        assert response.status_code == 200
        data = response.json()
        assert "scope" in data
        assert "rankings" in data
    
    def test_get_country_rankings(self):
        """Obtener rankings por país"""
        response = client.get("/api/risk/rankings?scope=country")
        
        assert response.status_code == 200
    
    def test_invalid_ranking_scope(self):
        """Scope de ranking inválido"""
        response = client.get("/api/risk/rankings?scope=invalid")
        
        assert response.status_code == 422


class TestHotBorders:
    """Tests para fronteras calientes"""
    
    def test_get_hot_borders(self):
        """Obtener fronteras más disputadas"""
        response = client.get("/api/risk/borders/hot")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "borders" in data
    
    def test_hot_borders_with_limit(self):
        """Obtener fronteras con límite"""
        response = client.get("/api/risk/borders/hot?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["borders"]) <= 5


class TestConquestHistory:
    """Tests para historial de conquistas"""
    
    def test_get_conquest_history(self):
        """Obtener historial de conquistas"""
        response = client.get("/api/risk/history/conquests")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "conquests" in data
    
    def test_get_conquest_history_with_limit(self):
        """Historial con límite"""
        response = client.get("/api/risk/history/conquests?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["conquests"]) <= 10
    
    def test_get_territory_conquest_history(self):
        """Historial de conquistas de un territorio específico"""
        # Obtener un territorio
        map_response = client.get("/api/risk/map?zoom=world")
        territories = map_response.json()["territories"]
        
        if territories:
            territory_id = territories[0]["id"]
            
            response = client.get(
                f"/api/risk/history/conquests?territory_id={territory_id}"
            )
            
            assert response.status_code == 200


class TestUserImpact:
    """Tests para impacto del usuario"""
    
    def test_get_user_impact(self, authenticated_user):
        """Obtener resumen de impacto"""
        response = client.get(
            "/api/risk/user/impact",
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_moves" in data
        assert "critical_moves" in data
        assert "conquests_participated" in data
        assert "territories_impacted" in data
        assert "total_units_deployed" in data
        assert "total_km_allocated" in data
    
    def test_get_strategic_suggestions(self, authenticated_user):
        """Obtener sugerencias estratégicas"""
        response = client.get(
            "/api/risk/user/suggestions",
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)


class TestAttackPreview:
    """Tests para previsualización de ataques"""
    
    def test_preview_attack(self):
        """Previsualizar ataque a territorio"""
        # Obtener un territorio
        map_response = client.get("/api/risk/map?zoom=world")
        territories = map_response.json()["territories"]
        
        if territories:
            territory_id = territories[0]["id"]
            
            response = client.get(
                f"/api/risk/preview/battle/{territory_id}?units=10"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "territory_name" in data
            assert "current_units" in data
            assert "attack_units" in data
            assert "success_probability" in data
            assert "estimated_hexagons_conquered" in data
            assert "recommendation" in data
            assert data["recommendation"] in ["GO!", "RISKY", "AVOID"]
    
    def test_preview_massive_attack(self):
        """Previsualizar ataque masivo"""
        map_response = client.get("/api/risk/map?zoom=world")
        territories = map_response.json()["territories"]
        
        if territories:
            territory_id = territories[0]["id"]
            
            response = client.get(
                f"/api/risk/preview/battle/{territory_id}?units=1000"
            )
            
            assert response.status_code == 200
            data = response.json()
            # Con muchas unidades debería ser "GO!"
            assert data["success_probability"] > 50
    
    def test_preview_weak_attack(self):
        """Previsualizar ataque débil"""
        map_response = client.get("/api/risk/map?zoom=world")
        territories = map_response.json()["territories"]
        
        if territories:
            territory_id = territories[0]["id"]
            
            response = client.get(
                f"/api/risk/preview/battle/{territory_id}?units=1"
            )
            
            assert response.status_code == 200
            data = response.json()
            # Con pocas unidades debería ser "AVOID"
            assert data["recommendation"] == "AVOID"


class TestGlobalStats:
    """Tests para estadísticas globales"""
    
    def test_get_global_stats(self):
        """Obtener estadísticas globales"""
        response = client.get("/api/risk/stats/global")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_territories" in data
        assert "territories_under_attack" in data
        assert "active_battles" in data
        assert "conquests_today" in data
        assert "conquest_rate" in data
