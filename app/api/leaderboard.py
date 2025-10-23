# app/api/leaderboard.py

from fastapi import APIRouter, Query
from typing import Literal
from app.core.database import supabase

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/users")
async def get_users_leaderboard(
    metric: Literal["points", "km", "zones"] = "points",
    limit: int = Query(50, ge=1, le=100)
):
    """Ranking de usuarios"""
    
    metric_map = {
        "points": "total_points",
        "km": "total_km",
        "zones": "zones_controlled"
    }
    
    order_by = metric_map.get(metric, "total_points")
    
    response = supabase.table('users')\
        .select('id, username, avatar_url, total_points, total_km, zones_controlled, team_id')\
        .eq('is_active', True)\
        .order(order_by, desc=True)\
        .limit(limit)\
        .execute()
    
    # Añadir posición
    leaderboard = []
    for idx, user in enumerate(response.data, 1):
        leaderboard.append({
            **user,
            'rank': idx
        })
    
    return {
        "metric": metric,
        "total": len(leaderboard),
        "leaderboard": leaderboard
    }


@router.get("/teams")
async def get_teams_leaderboard(
    metric: Literal["points", "km", "zones"] = "points",
    limit: int = Query(50, ge=1, le=100)
):
    """Ranking de equipos"""
    
    metric_map = {
        "points": "total_points",
        "km": "total_km",
        "zones": "zones_controlled"
    }
    
    order_by = metric_map.get(metric, "total_points")
    
    response = supabase.table('teams')\
        .select('id, name, color, logo_url, total_points, total_km, zones_controlled, members_count')\
        .order(order_by, desc=True)\
        .limit(limit)\
        .execute()
    
    # Añadir posición
    leaderboard = []
    for idx, team in enumerate(response.data, 1):
        leaderboard.append({
            **team,
            'rank': idx
        })
    
    return {
        "metric": metric,
        "total": len(leaderboard),
        "leaderboard": leaderboard
    }


@router.get("/zones/most-active")
async def get_most_active_zones(limit: int = Query(50, ge=1, le=100)):
    """Zonas con más actividad"""
    
    response = supabase.table('zones')\
        .select('*, teams(name, color)')\
        .order('total_km', desc=True)\
        .limit(limit)\
        .execute()
    
    return {
        "total": len(response.data),
        "zones": response.data
    }


@router.get("/zones/most-contested")
async def get_most_contested_zones(limit: int = Query(50, ge=1, le=100)):
    """
    Zonas más disputadas (con más cambios de control)
    """
    
    # Contar cambios de control por zona
    response = supabase.rpc('get_most_contested_zones', {'result_limit': limit}).execute()
    
    # Si no existe el RPC, hacerlo manualmente
    if not response.data:
        zones_response = supabase.table('zone_control_history')\
            .select('zone_id, zones(*), COUNT(*) as changes')\
            .group_by('zone_id')\
            .order('changes', desc=True)\
            .limit(limit)\
            .execute()
        
        return {
            "total": len(zones_response.data),
            "zones": zones_response.data
        }
    
    return {
        "total": len(response.data),
        "zones": response.data
    }


@router.get("/user/{user_id}/rank")
async def get_user_rank(user_id: str):
    """Obtener posición del usuario en el ranking"""
    
    # Ranking por puntos
    all_users = supabase.table('users')\
        .select('id, total_points, total_km, zones_controlled')\
        .eq('is_active', True)\
        .order('total_points', desc=True)\
        .execute()
    
    user_rank = None
    for idx, user in enumerate(all_users.data, 1):
        if user['id'] == user_id:
            user_rank = idx
            break
    
    if user_rank is None:
        return {
            "user_id": user_id,
            "rank": None,
            "total_users": len(all_users.data)
        }
    
    return {
        "user_id": user_id,
        "rank": user_rank,
        "total_users": len(all_users.data),
        "percentile": round((1 - (user_rank / len(all_users.data))) * 100, 2)
    }


@router.get("/team/{team_id}/rank")
async def get_team_rank(team_id: str):
    """Obtener posición del equipo en el ranking"""
    
    all_teams = supabase.table('teams')\
        .select('id, total_points, total_km, zones_controlled')\
        .order('total_points', desc=True)\
        .execute()
    
    team_rank = None
    for idx, team in enumerate(all_teams.data, 1):
        if team['id'] == team_id:
            team_rank = idx
            break
    
    if team_rank is None:
        return {
            "team_id": team_id,
            "rank": None,
            "total_teams": len(all_teams.data)
        }
    
    return {
        "team_id": team_id,
        "rank": team_rank,
        "total_teams": len(all_teams.data),
        "percentile": round((1 - (team_rank / len(all_teams.data))) * 100, 2)
    }
