# app/api/competitions.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from app.models.competition import (
    Competition, CompetitionCreate, CompetitionWithStats,
    ActivityAllocationRequest, GeographicEntity, CompetitionScope
)
from app.api.deps import get_current_user
from app.core.database import supabase
from app.services.competition_service import competition_service

router = APIRouter(prefix="/competitions", tags=["competitions"])


@router.post("", response_model=Competition, status_code=status.HTTP_201_CREATED)
async def create_competition(
    competition_in: CompetitionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Crear nueva competición"""
    
    competition_data = competition_in.model_dump()
    competition_data['status'] = 'upcoming'
    
    response = supabase.table('competitions').insert(competition_data).execute()
    
    return response.data[0]


@router.get("", response_model=List[CompetitionWithStats])
async def list_competitions(
    status_filter: Optional[str] = Query(None, regex="^(upcoming|active|finished)$"),
    scope: Optional[CompetitionScope] = None,
    participant_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Listar competiciones"""
    
    query = supabase.table('competitions').select('*')
    
    if status_filter:
        query = query.eq('status', status_filter)
    if scope:
        query = query.eq('scope', scope)
    if participant_type:
        query = query.eq('participant_type', participant_type)
    
    response = query.order('start_date', desc=True).range(skip, skip + limit - 1).execute()
    
    # Enriquecer con stats
    competitions = []
    for comp in response.data:
        # Obtener stats
        stats_response = supabase.table('competition_participants')\
            .select('*')\
            .eq('competition_id', comp['id'])\
            .execute()
        
        comp['participant_count'] = len(stats_response.data)
        comp['total_km_competition'] = sum(p['total_km'] for p in stats_response.data)
        comp['total_activities'] = sum(p['activities_count'] for p in stats_response.data)
        
        # Top 3 participantes
        top = sorted(stats_response.data, key=lambda x: x['total_points'], reverse=True)[:3]
        comp['top_participants'] = top
        
        competitions.append(comp)
    
    return competitions


@router.get("/active/me")
async def get_my_active_competitions(
    current_user: dict = Depends(get_current_user)
):
    """Obtener competiciones activas relevantes para el usuario"""
    
    # TODO: Obtener ciudad del usuario (podría estar en perfil)
    user_city = None  # Implementar lógica para detectar ciudad
    
    competitions = await competition_service.get_active_competitions_for_user(
        user_id=current_user['id'],
        user_city=user_city
    )
    
    return {
        "total": len(competitions),
        "competitions": competitions
    }


@router.get("/{competition_id}", response_model=CompetitionWithStats)
async def get_competition(competition_id: str):
    """Obtener detalles de una competición"""
    
    response = supabase.table('competitions').select('*').eq('id', competition_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found"
        )
    
    competition = response.data[0]
    
    # Stats
    stats_response = supabase.table('competition_participants')\
        .select('*')\
        .eq('competition_id', competition_id)\
        .execute()
    
    competition['participant_count'] = len(stats_response.data)
    competition['total_km_competition'] = sum(p['total_km'] for p in stats_response.data)
    competition['total_activities'] = sum(p['activities_count'] for p in stats_response.data)
    
    top = sorted(stats_response.data, key=lambda x: x['total_points'], reverse=True)[:10]
    competition['top_participants'] = top
    
    return competition


@router.post("/{competition_id}/join")
async def join_competition(
    competition_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Unirse a una competición"""
    
    # Verificar que existe y está activa o próxima
    comp_response = supabase.table('competitions')\
        .select('*')\
        .eq('id', competition_id)\
        .execute()
    
    if not comp_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found"
        )
    
    competition = comp_response.data[0]
    
    if competition['status'] not in ['upcoming', 'active']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Competition is not accepting participants"
        )
    
    # Verificar si ya participa
    existing = supabase.table('competition_participants')\
        .select('id')\
        .eq('competition_id', competition_id)\
        .eq('participant_type', 'user')\
        .eq('participant_id', current_user['id'])\
        .execute()
    
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already participating in this competition"
        )
    
    # Verificar límite de participantes
    if competition.get('max_participants'):
        count_response = supabase.table('competition_participants')\
            .select('id', count='exact')\
            .eq('competition_id', competition_id)\
            .execute()
        
        if count_response.count >= competition['max_participants']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Competition is full"
            )
    
    # Añadir participante
    participant_data = {
        'competition_id': competition_id,
        'participant_type': 'user',
        'participant_id': current_user['id']
    }
    
    supabase.table('competition_participants').insert(participant_data).execute()
    
    return {"message": "Successfully joined competition", "competition_id": competition_id}


@router.post("/allocate", status_code=status.HTTP_201_CREATED)
async def allocate_activity_km(
    allocation_request: ActivityAllocationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Asignar KM de una actividad a competiciones
    Ejemplo: 5km -> 2km para Barcelona, 3km para Badalona
    """
    
    # Verificar que la actividad existe y pertenece al usuario
    activity_response = supabase.table('activities')\
        .select('*')\
        .eq('id', str(allocation_request.activity_id))\
        .eq('user_id', current_user['id'])\
        .execute()
    
    if not activity_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found or unauthorized"
        )
    
    activity = activity_response.data[0]
    
    # Procesar asignaciones
    result = await competition_service.allocate_activity_km(
        activity_id=allocation_request.activity_id,
        user_id=current_user['id'],
        allocations=allocation_request.allocations,
        total_activity_km=activity['distance_km']
    )
    
    return result


@router.get("/{competition_id}/leaderboard")
async def get_competition_leaderboard(
    competition_id: str,
    limit: int = Query(50, ge=1, le=200)
):
    """Obtener ranking de una competición"""
    
    leaderboard = await competition_service.get_competition_leaderboard(
        competition_id=competition_id,
        limit=limit
    )
    
    return {
        "competition_id": competition_id,
        "total": len(leaderboard),
        "leaderboard": leaderboard
    }


@router.get("/{competition_id}/my-rank")
async def get_my_competition_rank(
    competition_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtener mi posición en una competición"""
    
    participant = supabase.table('competition_participants')\
        .select('*')\
        .eq('competition_id', competition_id)\
        .eq('participant_type', 'user')\
        .eq('participant_id', current_user['id'])\
        .execute()
    
    if not participant.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not participating in this competition"
        )
    
    return participant.data[0]


# ==========================================
# ENTIDADES GEOGRÁFICAS (Ciudades, Países)
# ==========================================

@router.get("/geo/cities", response_model=List[GeographicEntity])
async def list_cities(
    country: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500)
):
    """Listar ciudades"""
    
    query = supabase.table('geographic_entities')\
        .select('*')\
        .eq('entity_type', 'city')
    
    if country:
        # Buscar parent country
        country_response = supabase.table('geographic_entities')\
            .select('id')\
            .eq('name', country)\
            .eq('entity_type', 'country')\
            .execute()
        
        if country_response.data:
            query = query.eq('country_id', country_response.data[0]['id'])
    
    response = query.order('total_km', desc=True).limit(limit).execute()
    
    return response.data


@router.get("/geo/countries", response_model=List[GeographicEntity])
async def list_countries():
    """Listar países"""
    
    response = supabase.table('geographic_entities')\
        .select('*')\
        .eq('entity_type', 'country')\
        .order('total_km', desc=True)\
        .execute()
    
    return response.data


@router.get("/geo/rankings/cities")
async def get_city_rankings(limit: int = Query(50, ge=1, le=100)):
    """Ranking global de ciudades"""
    
    response = supabase.table('geographic_entities')\
        .select('*')\
        .eq('entity_type', 'city')\
        .order('total_km', desc=True)\
        .limit(limit)\
        .execute()
    
    rankings = []
    for idx, city in enumerate(response.data, 1):
        city['rank'] = idx
        rankings.append(city)
    
    return {
        "total": len(rankings),
        "rankings": rankings
    }


@router.get("/geo/rankings/countries")
async def get_country_rankings(limit: int = Query(50, ge=1, le=100)):
    """Ranking global de países"""
    
    response = supabase.table('geographic_entities')\
        .select('*')\
        .eq('entity_type', 'country')\
        .order('total_km', desc=True)\
        .limit(limit)\
        .execute()
    
    rankings = []
    for idx, country in enumerate(response.data, 1):
        country['rank'] = idx
        rankings.append(country)
    
    return {
        "total": len(rankings),
        "rankings": rankings
    }


@router.get("/geo/battle/{city1}/{city2}")
async def get_city_battle(city1: str, city2: str):
    """
    Batalla entre dos ciudades
    Ejemplo: Barcelona vs Badalona
    """
    
    battle = await competition_service.get_city_battle(city1, city2)
    
    if not battle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both cities not found"
        )
    
    return battle


@router.get("/geo/user-stats")
async def get_user_geographic_stats(
    current_user: dict = Depends(get_current_user)
):
    """Obtener stats del usuario en todas las entidades geográficas"""
    
    stats_response = supabase.table('user_geographic_stats')\
        .select('*, geographic_entities(*)')\
        .eq('user_id', current_user['id'])\
        .execute()
    
    # Agrupar por tipo de entidad
    stats_by_type = {
        'cities': [],
        'regions': [],
        'countries': []
    }
    
    for stat in stats_response.data:
        entity = stat.get('geographic_entities')
        if entity:
            entity_type = entity['entity_type']
            if entity_type == 'city':
                stats_by_type['cities'].append({**stat, 'entity_name': entity['name']})
            elif entity_type == 'region':
                stats_by_type['regions'].append({**stat, 'entity_name': entity['name']})
            elif entity_type == 'country':
                stats_by_type['countries'].append({**stat, 'entity_name': entity['name']})
    
    return stats_by_type
