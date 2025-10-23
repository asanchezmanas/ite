# app/api/activities.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from app.models.activity import Activity, ActivityCreate, ActivityWithZones
from app.api.deps import get_current_user
from app.services.activity_processor import activity_processor

router = APIRouter(prefix="/activities", tags=["activities"])


@router.post("", response_model=ActivityWithZones, status_code=status.HTTP_201_CREATED)
async def create_activity(
    activity_in: ActivityCreate,
    current_user: dict = Depends(get_current_user)
):
    """Crear nueva actividad"""
    
    activity = await activity_processor.create_activity(
        user_id=current_user['id'],
        activity_type=activity_in.activity_type,
        distance_km=activity_in.distance_km,
        duration_minutes=activity_in.duration_minutes,
        recorded_at=activity_in.recorded_at,
        polyline=activity_in.polyline,
        start_lat=activity_in.start_lat,
        start_lng=activity_in.start_lng,
        avg_pace=activity_in.avg_pace,
        calories=activity_in.calories,
        elevation_gain=activity_in.elevation_gain,
        is_gym_activity=activity_in.is_gym_activity,
        assigned_zones=activity_in.assigned_zones,
        source='manual'
    )
    
    return activity


@router.get("/me", response_model=List[Activity])
async def get_my_activities(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Obtener actividades del usuario actual"""
    
    activities = await activity_processor.get_user_activities(
        user_id=current_user['id'],
        limit=limit,
        offset=skip
    )
    
    return activities


@router.get("/team", response_model=List[Activity])
async def get_team_activities(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Obtener actividades del equipo"""
    
    if not current_user.get('team_id'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not in any team"
        )
    
    activities = await activity_processor.get_team_activities(
        team_id=current_user['team_id'],
        limit=limit,
        offset=skip
    )
    
    return activities


@router.get("/{activity_id}", response_model=Activity)
async def get_activity(activity_id: str):
    """Obtener detalles de una actividad"""
    
    from app.core.database import supabase
    
    response = supabase.table('activities').select('*').eq('id', activity_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    return response.data[0]


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Eliminar actividad"""
    
    success = await activity_processor.delete_activity(
        activity_id=activity_id,
        user_id=current_user['id']
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found or unauthorized"
        )
    
    return None
