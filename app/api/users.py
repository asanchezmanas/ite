# app/api/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models.user import User, UserUpdate, UserPublic
from app.api.deps import get_current_user
from app.core.database import supabase

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Obtener perfil del usuario actual"""
    return current_user


@router.put("/me", response_model=User)
async def update_me(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Actualizar perfil del usuario actual"""
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    if not update_data:
        return current_user
    
    # Si cambia de equipo, verificar que existe
    if 'team_id' in update_data and update_data['team_id']:
        team_check = supabase.table('teams').select('id').eq('id', str(update_data['team_id'])).execute()
        if not team_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
    
    response = supabase.table('users').update(update_data).eq('id', current_user['id']).execute()
    
    return response.data[0]


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: str):
    """Obtener perfil público de usuario"""
    
    response = supabase.table('users').select(
        'id, username, full_name, avatar_url, total_km, total_points, zones_controlled, team_id'
    ).eq('id', user_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return response.data[0]


@router.get("/{user_id}/achievements")
async def get_user_achievements(user_id: str):
    """Obtener logros del usuario"""
    
    response = supabase.table('user_achievements')\
        .select('*, achievements(*)')\
        .eq('user_id', user_id)\
        .execute()
    
    return response.data


@router.get("/{user_id}/zones")
async def get_user_zones(user_id: str):
    """Obtener zonas controladas por usuario"""
    
    response = supabase.table('zones')\
        .select('*')\
        .eq('controlled_by_user', user_id)\
        .execute()
    
    return {
        "total": len(response.data),
        "zones": response.data
    }
