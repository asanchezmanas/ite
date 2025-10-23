# app/api/zones.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.models.zone import Zone, ZoneDetail, ZoneCreate
from app.api.deps import get_current_user, get_optional_user
from app.core.database import supabase
from app.services.zone_control import zone_control_service
from app.services.h3_service import h3_service

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("", response_model=List[Zone])
async def list_zones(
    lat: Optional[float] = Query(None, ge=-90, le=90),
    lng: Optional[float] = Query(None, ge=-180, le=180),
    radius_km: Optional[float] = Query(None, ge=0.1, le=50),
    city: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Listar zonas
    - Si se provee lat/lng/radius: zonas en ese área
    - Si se provee city: zonas de esa ciudad
    - Si no: todas las zonas (paginado)
    """
    
    if lat and lng and radius_km:
        # Zonas en área específica
        zones = await zone_control_service.get_zones_in_area(lat, lng, radius_km)
        return zones
    
    query = supabase.table('zones').select('*')
    
    if city:
        query = query.eq('city', city)
    
    response = query.order('total_km', desc=True).range(skip, skip + limit - 1).execute()
    
    return response.data


@router.get("/{zone_id}", response_model=ZoneDetail)
async def get_zone(zone_id: str):
    """Obtener detalles de una zona"""
    
    zone_response = supabase.table('zones').select('*').eq('id', zone_id).execute()
    
    if not zone_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found"
        )
    
    zone = zone_response.data[0]
    
    # Obtener top contributors
    contributors_response = supabase.table('zone_activities')\
        .select('user_id, users(username, avatar_url), SUM(distance_km) as total_km')\
        .eq('zone_id', zone_id)\
        .group_by('user_id')\
        .order('total_km', desc=True)\
        .limit(10)\
        .execute()
    
    zone['top_contributors'] = contributors_response.data if contributors_response.data else []
    
    # Obtener actividades recientes
    activities_response = supabase.table('zone_activities')\
        .select('*, users(username, avatar_url)')\
        .eq('zone_id', zone_id)\
        .order('recorded_at', desc=True)\
        .limit(20)\
        .execute()
    
    zone['recent_activities'] = activities_response.data if activities_response.data else []
    
    return zone


@router.get("/{zone_id}/boundary")
async def get_zone_boundary(zone_id: str):
    """Obtener coordenadas del perímetro del hexágono"""
    
    zone_response = supabase.table('zones').select('h3_index').eq('id', zone_id).execute()
    
    if not zone_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found"
        )
    
    h3_index = zone_response.data[0]['h3_index']
    boundary = h3_service.cell_to_boundary(h3_index)
    
    return {
        "h3_index": h3_index,
        "boundary": [{"lat": lat, "lng": lng} for lat, lng in boundary]
    }


@router.post("/initialize", status_code=status.HTTP_201_CREATED)
async def initialize_city_zones(
    center_lat: float = Query(..., ge=-90, le=90),
    center_lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(..., ge=0.1, le=50),
    city: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Inicializar zonas de una ciudad (admin only)
    Crea hexágonos en el área especificada
    """
    
    # TODO: Verificar que el usuario es admin
    
    # Obtener H3 cells del área
    h3_indexes = h3_service.get_area_cells(center_lat, center_lng, radius_km)
    
    zones_created = 0
    zones_existing = 0
    
    for h3_index in h3_indexes:
        # Verificar si ya existe
        existing = supabase.table('zones').select('id').eq('h3_index', h3_index).execute()
        
        if existing.data:
            zones_existing += 1
            continue
        
        # Crear zona
        lat, lng = h3_service.cell_to_lat_lng(h3_index)
        
        zone_data = {
            'h3_index': h3_index,
            'center_lat': lat,
            'center_lng': lng,
            'city': city
        }
        
        supabase.table('zones').insert(zone_data).execute()
        zones_created += 1
    
    return {
        "message": "Zones initialized successfully",
        "total_zones": len(h3_indexes),
        "created": zones_created,
        "existing": zones_existing,
        "stats": h3_service.get_city_stats(h3_indexes)
    }


@router.get("/h3/{h3_index}", response_model=Zone)
async def get_zone_by_h3(h3_index: str):
    """Obtener zona por H3 index"""
    
    if not h3_service.is_valid_cell(h3_index):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid H3 index"
        )
    
    response = supabase.table('zones').select('*').eq('h3_index', h3_index).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found"
        )
    
    return response.data[0]


@router.get("/map/tiles")
async def get_map_tiles(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(5, ge=0.1, le=50)
):
    """
    Obtener tiles del mapa para renderizar
    Retorna hexágonos con sus estados de control
    """
    
    zones = await zone_control_service.get_zones_in_area(lat, lng, radius_km)
    
    tiles = []
    for zone in zones:
        boundary = h3_service.cell_to_boundary(zone['h3_index'])
        
        tiles.append({
            'id': zone['id'],
            'h3_index': zone['h3_index'],
            'boundary': [{'lat': lat, 'lng': lng} for lat, lng in boundary],
            'center': {'lat': zone['center_lat'], 'lng': zone['center_lng']},
            'controlled_by_team': zone.get('controlled_by_team'),
            'controlled_by_user': zone.get('controlled_by_user'),
            'control_percentage': zone.get('control_percentage', 0),
            'is_poi': zone.get('is_poi', False),
            'poi_name': zone.get('poi_name')
        })
    
    return {
        'total': len(tiles),
        'tiles': tiles
    }
