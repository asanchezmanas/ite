# app/services/zone_control.py

from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime, timedelta
from app.core.database import supabase
from app.core.config import settings
from app.services.h3_service import h3_service


class ZoneControlService:
    """Servicio para gestionar control de zonas"""
    
    async def process_activity_zones(
        self,
        activity_id: UUID,
        user_id: UUID,
        team_id: Optional[UUID],
        h3_indexes: List[str],
        distance_km: float,
        recorded_at: datetime,
        is_gym: bool = False
    ) -> List[Dict]:
        """
        Procesar actividad y actualizar control de zonas
        Retorna lista de zonas afectadas
        """
        affected_zones = []
        
        # Distribuir distancia entre zonas
        km_per_zone = distance_km / len(h3_indexes) if h3_indexes else 0
        
        # Aplicar multiplicador si es gym
        if is_gym:
            km_per_zone *= settings.GYM_ACTIVITY_MULTIPLIER
        
        for h3_index in h3_indexes:
            # Obtener o crear zona
            zone = await self._get_or_create_zone(h3_index)
            
            # Calcular puntos (aplicar bonus si es POI)
            points = int(km_per_zone * settings.ACTIVITY_POINTS_PER_KM * zone['bonus_multiplier'])
            
            # Aplicar bonus de equipo
            if team_id:
                points = int(points * settings.TEAM_ACTIVITY_BONUS)
            
            # Registrar actividad en zona
            zone_activity = await self._create_zone_activity(
                zone_id=zone['id'],
                activity_id=activity_id,
                user_id=user_id,
                team_id=team_id,
                distance_km=km_per_zone,
                points_earned=points,
                recorded_at=recorded_at
            )
            
            # Recalcular control de zona
            control_changed = await self._recalculate_zone_control(
                zone_id=zone['id'],
                user_id=user_id,
                team_id=team_id
            )
            
            affected_zones.append({
                'zone_id': zone['id'],
                'h3_index': h3_index,
                'distance_km': km_per_zone,
                'points_earned': points,
                'control_changed': control_changed,
                'controlled_by_team': zone.get('controlled_by_team'),
                'controlled_by_user': zone.get('controlled_by_user')
            })
        
        return affected_zones
    
    async def _get_or_create_zone(self, h3_index: str) -> Dict:
        """Obtener zona o crearla si no existe"""
        # Buscar zona existente
        response = supabase.table('zones').select('*').eq('h3_index', h3_index).execute()
        
        if response.data:
            return response.data[0]
        
        # Crear nueva zona
        lat, lng = h3_service.cell_to_lat_lng(h3_index)
        
        new_zone = {
            'h3_index': h3_index,
            'center_lat': lat,
            'center_lng': lng,
            # TODO: Obtener ciudad/distrito con reverse geocoding
            'city': None,
            'district': None
        }
        
        response = supabase.table('zones').insert(new_zone).execute()
        return response.data[0]
    
    async def _create_zone_activity(
        self,
        zone_id: UUID,
        activity_id: UUID,
        user_id: UUID,
        team_id: Optional[UUID],
        distance_km: float,
        points_earned: int,
        recorded_at: datetime
    ) -> Dict:
        """Registrar actividad en zona específica"""
        zone_activity = {
            'zone_id': str(zone_id),
            'activity_id': str(activity_id),
            'user_id': str(user_id),
            'team_id': str(team_id) if team_id else None,
            'distance_km': distance_km,
            'points_earned': points_earned,
            'recorded_at': recorded_at.isoformat()
        }
        
        response = supabase.table('zone_activities').insert(zone_activity).execute()
        
        # Actualizar stats de zona
        supabase.table('zones').update({
            'total_km': supabase.raw('total_km + ' + str(distance_km)),
            'total_activities': supabase.raw('total_activities + 1')
        }).eq('id', str(zone_id)).execute()
        
        return response.data[0]
    
    async def _recalculate_zone_control(
        self,
        zone_id: UUID,
        user_id: UUID,
        team_id: Optional[UUID]
    ) -> bool:
        """
        Recalcular control de zona basado en actividad reciente
        Retorna True si cambió el control
        """
        # Obtener zona actual
        zone_response = supabase.table('zones').select('*').eq('id', str(zone_id)).execute()
        zone = zone_response.data[0]
        
        # Ventana de tiempo para calcular control (últimos 30 días)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Obtener actividad por equipo en ventana de tiempo
        activities_response = supabase.table('zone_activities')\
            .select('team_id, user_id, distance_km')\
            .eq('zone_id', str(zone_id))\
            .gte('recorded_at', cutoff_date.isoformat())\
            .execute()
        
        if not activities_response.data:
            return False
        
        # Calcular km por equipo/usuario
        team_km = {}
        user_km = {}
        
        for activity in activities_response.data:
            tid = activity.get('team_id')
            uid = activity['user_id']
            km = activity['distance_km']
            
            if tid:
                team_km[tid] = team_km.get(tid, 0) + km
            user_km[uid] = user_km.get(uid, 0) + km
        
        # Determinar controlador (equipo con más km)
        if team_km:
            controlling_team = max(team_km.items(), key=lambda x: x[1])
            total_km = sum(team_km.values())
            
            # Aplicar bonus de defensa si ya controla
            if zone['controlled_by_team'] == controlling_team[0]:
                controlling_km = controlling_team[1] * settings.ZONE_DEFENSE_MULTIPLIER
            else:
                controlling_km = controlling_team[1]
            
            control_percentage = min(100, (controlling_km / total_km) * 100)
            
            # Cambiar control si supera threshold
            changed = False
            if control_percentage >= 50 and controlling_km >= settings.ZONE_CONTROL_THRESHOLD_KM:
                new_team = controlling_team[0]
                changed = zone['controlled_by_team'] != new_team
                
                # Actualizar zona
                update_data = {
                    'controlled_by_team': new_team,
                    'control_percentage': round(control_percentage, 2)
                }
                
                # Determinar usuario top en ese equipo
                team_users = {k: v for k, v in user_km.items() 
                            if any(a['user_id'] == k and a.get('team_id') == new_team 
                                 for a in activities_response.data)}
                if team_users:
                    update_data['controlled_by_user'] = max(team_users.items(), key=lambda x: x[1])[0]
                
                supabase.table('zones').update(update_data).eq('id', str(zone_id)).execute()
                
                # Registrar cambio en historial
                if changed:
                    await self._log_control_change(
                        zone_id=zone_id,
                        previous_team=zone.get('controlled_by_team'),
                        new_team=new_team
                    )
                
                return changed
        
        return False
    
    async def _log_control_change(
        self,
        zone_id: UUID,
        previous_team: Optional[str],
        new_team: str
    ):
        """Registrar cambio de control en historial"""
        history_entry = {
            'zone_id': str(zone_id),
            'previous_team': previous_team,
            'new_team': new_team
        }
        
        supabase.table('zone_control_history').insert(history_entry).execute()
    
    async def get_user_zones(self, user_id: UUID) -> List[Dict]:
        """Obtener zonas controladas por usuario"""
        response = supabase.table('zones')\
            .select('*')\
            .eq('controlled_by_user', str(user_id))\
            .execute()
        
        return response.data
    
    async def get_team_zones(self, team_id: UUID) -> List[Dict]:
        """Obtener zonas controladas por equipo"""
        response = supabase.table('zones')\
            .select('*')\
            .eq('controlled_by_team', str(team_id))\
            .execute()
        
        return response.data
    
    async def get_zones_in_area(
        self,
        center_lat: float,
        center_lng: float,
        radius_km: float
    ) -> List[Dict]:
        """Obtener zonas en un área específica"""
        # Obtener H3 cells en el área
        h3_indexes = h3_service.get_area_cells(center_lat, center_lng, radius_km)
        
        # Buscar en BD
        response = supabase.table('zones')\
            .select('*')\
            .in_('h3_index', h3_indexes)\
            .execute()
        
        return response.data


# Instancia global
zone_control_service = ZoneControlService()
