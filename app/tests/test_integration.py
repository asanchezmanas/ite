# app/tests/test_integration.py

"""
Tests de integración completos que prueban flujos end-to-end
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app

client = TestClient(app)


@pytest.mark.integration
class TestCompleteUserJourney:
    """Test del journey completo de un usuario"""
    
    def test_complete_user_flow(self):
        """
        Flujo completo: Registro → Actividad → Equipo → Conquista
        """
        # 1. REGISTRO
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "journey@example.com",
                "username": "journeyuser",
                "password": "Pass123"
            }
        )
        assert register_response.status_code == 201
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. VER PERFIL
        profile_response = client.get("/api/users/me", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["username"] == "journeyuser"
        assert profile_response.json()["total_km"] == 0
        
        # 3. CREAR EQUIPO
        team_response = client.post(
            "/api/teams",
            headers=headers,
            json={
                "name": "Journey Team",
                "color": "#00FF00"
            }
        )
        assert team_response.status_code == 201
        team_id = team_response.json()["id"]
        
        # 4. CREAR PRIMERA ACTIVIDAD
        activity_response = client.post(
            "/api/activities",
            headers=headers,
            json={
                "activity_type": "run",
                "distance_km": 10.0,
                "duration_minutes": 50,
                "recorded_at": datetime.utcnow().isoformat()
            }
        )
        assert activity_response.status_code == 201
        activity_id = activity_response.json()["id"]
        
        # 5. VERIFICAR ACTUALIZACIÓN DE STATS
        updated_profile = client.get("/api/users/me", headers=headers).json()
        assert updated_profile["total_km"] == 10.0
        assert updated_profile["total_points"] > 0
        
        # 6. VER MAPA RISK
        map_response = client.get("/api/risk/map?zoom=world")
        assert map_response.status_code == 200
        
        # 7. VER SUGERENCIAS ESTRATÉGICAS
        suggestions_response = client.get(
            "/api/risk/user/suggestions",
            headers=headers
        )
        assert suggestions_response.status_code == 200
        
        # 8. EJECUTAR ATAQUE
        if map_response.json()["territories"]:
            target_territory = map_response.json()["territories"][0]["id"]
            
            move_response = client.post(
                "/api/risk/move",
                headers=headers,
                json={
                    "activity_id": activity_id,
                    "move_type": "attack",
                    "to_territory_id": target_territory,
                    "units": 10,
                    "km": 10.0
                }
            )
            assert move_response.status_code == 200
        
        # 9. VER IMPACTO
        impact_response = client.get(
            "/api/risk/user/impact",
            headers=headers
        )
        assert impact_response.status_code == 200
        assert impact_response.json()["total_moves"] > 0


@pytest.mark.integration
class TestTeamCollaboration:
    """Test de colaboración en equipo"""
    
    def test_team_conquest_flow(self):
        """
        Varios usuarios en un equipo conquistando territorio
        """
        # Crear equipo y 3 usuarios
        users = []
        team_id = None
        
        for i in range(3):
            # Registrar usuario
            register_response = client.post(
                "/api/auth/register",
                json={
                    "email": f"teamuser{i}@example.com",
                    "username": f"teamuser{i}",
                    "password": "Pass123"
                }
            )
            token = register_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            if i == 0:
                # Primer usuario crea el equipo
                team_response = client.post(
                    "/api/teams",
                    headers=headers,
                    json={
                        "name": "Conquest Team",
                        "color": "#FF0000"
                    }
                )
                team_id = team_response.json()["id"]
            else:
                # Otros usuarios se unen
                client.post(f"/api/teams/{team_id}/join", headers=headers)
            
            users.append({"headers": headers, "username": f"teamuser{i}"})
        
        # Cada usuario registra actividad
        for user in users:
            activity_response = client.post(
                "/api/activities",
                headers=user["headers"],
                json={
                    "activity_type": "run",
                    "distance_km": 10.0,
                    "recorded_at": datetime.utcnow().isoformat()
                }
            )
            assert activity_response.status_code == 201
        
        # Verificar stats del equipo
        team_detail = client.get(f"/api/teams/{team_id}").json()
        assert team_detail["members_count"] == 3
        assert team_detail["total_km"] == 30.0  # 10 km x 3 usuarios


@pytest.mark.integration
class TestBattleScenario:
    """Test de escenario de batalla"""
    
    def test_territory_battle(self):
        """
        Simular batalla entre dos equipos por un territorio
        """
        # Crear dos equipos
        teams = []
        for i in range(2):
            register_response = client.post(
                "/api/auth/register",
                json={
                    "email": f"leader{i}@example.com",
                    "username": f"leader{i}",
                    "password": "Pass123"
                }
            )
            token = register_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            team_response = client.post(
                "/api/teams",
                headers=headers,
                json={
                    "name": f"Battle Team {i}",
                    "color": "#FF0000" if i == 0 else "#0000FF"
                }
            )
            
            teams.append({
                "headers": headers,
                "team_id": team_response.json()["id"]
            })
        
        # Obtener territorio objetivo
        map_response = client.get("/api/risk/map?zoom=world")
        if not map_response.json()["territories"]:
            return
        
        target_territory = map_response.json()["territories"][0]["id"]
        
        # Cada equipo ataca el mismo territorio
        for team in teams:
            # Crear actividad
            activity_response = client.post(
                "/api/activities",
                headers=team["headers"],
                json={
                    "activity_type": "run",
                    "distance_km": 20.0,
                    "recorded_at": datetime.utcnow().isoformat()
                }
            )
            activity_id = activity_response.json()["id"]
            
            # Atacar territorio
            client.post(
                "/api/risk/move",
                headers=team["headers"],
                json={
                    "activity_id": activity_id,
                    "move_type": "attack",
                    "to_territory_id": target_territory,
                    "units": 20,
                    "km": 20.0
                }
            )
        
        # Verificar que hay batalla activa
        battles_response = client.get("/api/risk/battles")
        assert battles_response.status_code == 200


@pytest.mark.integration
class TestStravaIntegration:
    """Tests de integración con Strava (mock)"""
    
    def test_strava_connection_flow(self):
        """
        Flujo de conexión con Strava
        """
        # Registrar usuario
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "strava@example.com",
                "username": "stravauser",
                "password": "Pass123"
            }
        )
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Obtener URL de autorización
        auth_url_response = client.get(
            "/api/integrations/strava/authorize",
            headers=headers
        )
        assert auth_url_response.status_code == 200
        assert "authorization_url" in auth_url_response.json()
        
        # Verificar estado de conexión (no conectado)
        status_response = client.get(
            "/api/integrations/strava/status",
            headers=headers
        )
        assert status_response.status_code == 200
        assert status_response.json()["connected"] is False


@pytest.mark.integration
class TestRankingsAndLeaderboards:
    """Tests de rankings y leaderboards"""
    
    def test_global_rankings_flow(self):
        """
        Crear usuarios, actividades y verificar rankings
        """
        users = []
        
        # Crear 5 usuarios con diferentes cantidades de KM
        for i in range(5):
            register_response = client.post(
                "/api/auth/register",
                json={
                    "email": f"rank{i}@example.com",
                    "username": f"rank{i}",
                    "password": "Pass123"
                }
            )
            token = register_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Cada usuario corre diferentes distancias
            distance = 10.0 * (i + 1)  # 10, 20, 30, 40, 50 km
            
            client.post(
                "/api/activities",
                headers=headers,
                json={
                    "activity_type": "run",
                    "distance_km": distance,
                    "recorded_at": datetime.utcnow().isoformat()
                }
            )
            
            users.append({
                "username": f"rank{i}",
                "expected_km": distance,
                "headers": headers
            })
        
        # Obtener ranking de usuarios
        leaderboard_response = client.get("/api/leaderboard/users?metric=km")
        assert leaderboard_response.status_code == 200
        
        leaderboard = leaderboard_response.json()["leaderboard"]
        
        # Verificar que están ordenados por KM descendente
        assert len(leaderboard) >= 5
        for i in range(len(leaderboard) - 1):
            assert leaderboard[i]["total_km"] >= leaderboard[i + 1]["total_km"]


@pytest.mark.integration
class TestAchievementsUnlock:
    """Tests de desbloqueo de logros"""
    
    def test_achievement_unlock_flow(self):
        """
        Desbloquear logros mediante actividades
        """
        # Registrar usuario
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "achiever@example.com",
                "username": "achiever",
                "password": "Pass123"
            }
        )
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        user_id = register_response.json()["user_id"] if "user_id" in register_response.json() else None
        
        # Crear primera actividad (debería desbloquear "Primeros Pasos")
        client.post(
            "/api/activities",
            headers=headers,
            json={
                "activity_type": "run",
                "distance_km": 5.0,
                "recorded_at": datetime.utcnow().isoformat()
            }
        )
        
        # Verificar logros desbloqueados
        if user_id:
            achievements_response = client.get(
                f"/api/users/{user_id}/achievements"
            )
            assert achievements_response.status_code == 200


@pytest.mark.slow
@pytest.mark.integration
class TestPerformance:
    """Tests de rendimiento"""
    
    def test_bulk_activities_creation(self):
        """
        Crear muchas actividades y verificar rendimiento
        """
        import time
        
        # Registrar usuario
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "bulk@example.com",
                "username": "bulkuser",
                "password": "Pass123"
            }
        )
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Crear 10 actividades
        start_time = time.time()
        
        for i in range(10):
            client.post(
                "/api/activities",
                headers=headers,
                json={
                    "activity_type": "run",
                    "distance_km": 10.0,
                    "recorded_at": datetime.utcnow().isoformat()
                }
            )
        
        elapsed_time = time.time() - start_time
        
        # Debería completarse en menos de 10 segundos
        assert elapsed_time < 10.0
        
        # Verificar que todas se crearon
        activities_response = client.get("/api/activities/me", headers=headers)
        assert len(activities_response.json()) == 10
