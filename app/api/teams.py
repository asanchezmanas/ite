# app/api/teams.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.models.team import Team, TeamCreate, TeamUpdate, TeamWithMembers
from app.api.deps import get_current_user
from app.core.database import supabase

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("", response_model=Team, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_in: TeamCreate,
    current_user: dict = Depends(get_current_user)
):
    """Crear nuevo equipo"""
    
    # Verificar nombre único
    name_check = supabase.table('teams').select('id').eq('name', team_in.name).execute()
    if name_check.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team name already taken"
        )
    
    team_data = team_in.model_dump()
    team_data['created_by'] = current_user['id']
    
    response = supabase.table('teams').insert(team_data).execute()
    team = response.data[0]
    
    # Unir al creador automáticamente
    supabase.table('users').update({'team_id': team['id']}).eq('id', current_user['id']).execute()
    
    return team


@router.get("", response_model=List[Team])
async def list_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    public_only: bool = True
):
    """Listar equipos"""
    
    query = supabase.table('teams').select('*')
    
    if public_only:
        query = query.eq('is_public', True)
    
    response = query.order('total_points', desc=True).range(skip, skip + limit - 1).execute()
    
    return response.data


@router.get("/{team_id}", response_model=TeamWithMembers)
async def get_team(team_id: str):
    """Obtener detalles del equipo"""
    
    team_response = supabase.table('teams').select('*').eq('id', team_id).execute()
    
    if not team_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    team = team_response.data[0]
    
    # Obtener miembros
    members_response = supabase.table('users')\
        .select('id, username, avatar_url, total_km, total_points')\
        .eq('team_id', team_id)\
        .order('total_points', desc=True)\
        .execute()
    
    team['members'] = members_response.data
    
    return team


@router.put("/{team_id}", response_model=Team)
async def update_team(
    team_id: str,
    team_update: TeamUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Actualizar equipo (solo creador)"""
    
    # Verificar que el equipo existe
    team_response = supabase.table('teams').select('*').eq('id', team_id).execute()
    
    if not team_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    team = team_response.data[0]
    
    # Verificar que es el creador
    if team['created_by'] != current_user['id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team creator can update team"
        )
    
    update_data = team_update.model_dump(exclude_unset=True)
    
    if not update_data:
        return team
    
    response = supabase.table('teams').update(update_data).eq('id', team_id).execute()
    
    return response.data[0]


@router.post("/{team_id}/join", response_model=dict)
async def join_team(
    team_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Unirse a un equipo"""
    
    # Verificar que el equipo existe
    team_response = supabase.table('teams').select('*').eq('id', team_id).execute()
    
    if not team_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    team = team_response.data[0]
    
    # Verificar que es público
    if not team['is_public']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Team is private"
        )
    
    # Verificar límite de miembros
    if team['members_count'] >= team['max_members']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team is full"
        )
    
    # Unir usuario
    supabase.table('users').update({'team_id': team_id}).eq('id', current_user['id']).execute()
    
    return {"message": "Successfully joined team", "team_id": team_id}


@router.post("/leave", response_model=dict)
async def leave_team(current_user: dict = Depends(get_current_user)):
    """Salir del equipo actual"""
    
    if not current_user.get('team_id'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not in any team"
        )
    
    supabase.table('users').update({'team_id': None}).eq('id', current_user['id']).execute()
    
    return {"message": "Successfully left team"}


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Eliminar equipo (solo creador)"""
    
    # Verificar que el equipo existe
    team_response = supabase.table('teams').select('*').eq('id', team_id).execute()
    
    if not team_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    team = team_response.data[0]
    
    # Verificar que es el creador
    if team['created_by'] != current_user['id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team creator can delete team"
        )
    
    # Remover miembros del equipo
    supabase.table('users').update({'team_id': None}).eq('team_id', team_id).execute()
    
    # Eliminar equipo
    supabase.table('teams').delete().eq('id', team_id).execute()
    
    return None


@router.get("/{team_id}/zones")
async def get_team_zones(team_id: str):
    """Obtener zonas controladas por equipo"""
    
    response = supabase.table('zones')\
        .select('*')\
        .eq('controlled_by_team', team_id)\
        .execute()
    
    return {
        "total": len(response.data),
        "zones": response.data
    }
