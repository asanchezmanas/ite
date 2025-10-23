# app/services/activity_processor.py

from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime
from app.core.database import supabase
from app.core.config import settings
from app.services.h3_service import h3_service
from app.services.zone_control import zone_control_service


class ActivityProcessor:
    """Procesar y guardar actividades"""
    
    async def create_activity(
        self,
        user_id: UUID,
        activity_type: str,
        distance_km: float,
        duration_minutes: Optional[int],
        recorded_at: datetime,
        polyline: Optional[str] = None,
        start_lat: Optional[float] = None,
        start_lng: Optional[float] = None,
        avg_pace: Optional[float] = None,
        calories: Optional[int] = None,
        elevation_gain: Optional[int] = None,
        is_gym_activity: bool = False,
        assigned_zones: Optional[List[str]] = None,
        source: str = 'manual',
        external_id: Optional[str] = None
    ) -> Dict:
        """Crear nueva actividad y procesar zonas"""
        
        # Obtener team del usuario
        user_response = supabase.table('users').select('team_id').eq('id', str(user_id)).execute()
        team_id = user_response.data[0].get('team_id') if user_response.data else None
        
        # Determinar zonas afectadas
        h3_indexes = []
        
        if is_gym_activity and assigned_zones:
            # Actividad de gym: usar zonas asignadas
            h3_indexes = assigned_zones
        elif polyline:
            # Actividad con ruta GPS: extraer zonas del polyline
            h3_indexes = h3_service.polyline_to_cells(polyline)
        elif start_lat and start_lng:
            # Solo punto inicial: asignar zona inicial
            h3_indexes = [h3_service.lat_lng_to_cell(start_lat, start_lng)]
        
        # Calcular puntos base
        points_earned = int(distance_km * settings.ACTIVITY_POINTS_PER_KM)
        
        # Aplicar multiplicadores
        if is_gym_activity:
            points_earned = int(points_earned * settings.GYM_ACTIVITY_MULTIPLIER)
        if team_id:
            points_earned = int(points_earned * settings.TEAM_ACTIVITY_BONUS)
        
        # Crear actividad en BD
        activity_data = {
            'user_id': str(user_id),
            'team_id': str(team_id) if team_id else None,
            'activity_type': activity_type,
            'distance_km': distance_km,
            'duration_minutes': duration_minutes,
            'avg_pace': avg_pace,
            'calories': calories,
            'elevation_gain': elevation_gain,
            'start_lat': start_lat,
            'start_lng': start_lng,
            'polyline': polyline,
            'is_gym_activity': is_gym_activity,
            'assigned_zones': assigned_zones,
            'source': source,
            'external_id': external_id,
            'points_earned': points_earned,
            'recorded_at': recorded_at.isoformat(),
            'synced_at': datetime.utcnow().isoformat()
        }
        
        activity_response = supabase.table('activities').insert(activity_data).execute()
        activity = activity_response.data[0]
        
        # Procesar zonas si hay
        affected_zones = []
        if h3_indexes:
            affected_zones = await zone_control_service.process_activity_zones(
                activity_id=activity['id'],
                user_id=user_id,
                team_id=team_id,
                h3_indexes=h3_indexes,
                distance_km=distance_km,
                recorded_at=recorded_at,
                is_gym=is_gym_activity
            )
        
        # Verificar logros
        await self._check_achievements(user_id)
        
        # Actualizar stats geográficos (ciudades, países)
        if h3_indexes:
            from app.services.competition_service import competition_service
            zone_ids = [zone['zone_id'] for zone in affected_zones]
            await competition_service.update_geographic_stats(
                user_id=user_id,
                activity_km=distance_km,
                activity_points=points_earned,
                zone_ids=zone_ids
            )
        
        return {
            **activity,
            'affected_zones': affected_zones
        }
    
    async def _check_achievements(self, user_id: UUID):
        """Verificar y desbloquear logros del usuario"""
        # Obtener usuario
        user_response = supabase.table('users').select('*').eq('id', str(user_id)).execute()
        if not user_response.data:
            return
        
        user = user_response.data[0]
        
        # Obtener logros no desbloqueados
        unlocked_response = supabase.table('user_achievements')\
            .select('achievement_id')\
            .eq('user_id', str(user_id))\
            .execute()
        
        unlocked_ids = [a['achievement_id'] for a in unlocked_response.data]
        
        # Obtener todos los logros
        achievements_response = supabase.table('achievements').select('*').execute()
        
        for achievement in achievements_response.data:
            if achievement['id'] in unlocked_ids:
                continue
            
            # Verificar si cumple requisito
            requirement_type = achievement['requirement_type']
            requirement_value = achievement['requirement_value']
            
            unlocked = False
            
            if requirement_type == 'total_km':
                unlocked = user['total_km'] >= requirement_value
            elif requirement_type == 'zones_controlled':
                unlocked = user['zones_controlled'] >= requirement_value
            elif requirement_type == 'activities_count':
                # Contar actividades
                count_response = supabase.table('activities')\
                    .select('id', count='exact')\
                    .eq('user_id', str(user_id))\
                    .execute()
                unlocked = count_response.count >= requirement_value
            
            # Desbloquear si cumple
            if unlocked:
                supabase.table('user_achievements').insert({
                    'user_id': str(user_id),
                    'achievement_id': achievement['id']
                }).execute()
                
                # Dar puntos de recompensa
                if achievement['points_reward'] > 0:
                    supabase.table('users').update({
                        'total_points': supabase.raw(f"total_points + {achievement['points_reward']}")
                    }).eq('id', str(user_id)).execute()
    
    async def get_user_activities(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Obtener actividades del usuario"""
        response = supabase.table('activities')\
            .select('*')\
            .eq('user_id', str(user_id))\
            .order('recorded_at', desc=True)\
            .limit(limit)\
            .offset(offset)\
            .execute()
        
        return response.data
    
    async def get_team_activities(
        self,
        team_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Obtener actividades del equipo"""
        response = supabase.table('activities')\
            .select('*')\
            .eq('team_id', str(team_id))\
            .order('recorded_at', desc=True)\
            .limit(limit)\
            .offset(offset)\
            .execute()
        
        return response.data
    
    async def delete_activity(self, activity_id: UUID, user_id: UUID) -> bool:
        """Eliminar actividad (y recalcular zonas)"""
        # Verificar que la actividad pertenece al usuario
        activity_response = supabase.table('activities')\
            .select('*')\
            .eq('id', str(activity_id))\
            .eq('user_id', str(user_id))\
            .execute()
        
        if not activity_response.data:
            return False
        
        activity = activity_response.data[0]
        
        # Eliminar actividad (cascade eliminará zone_activities)
        supabase.table('activities').delete().eq('id', str(activity_id)).execute()
        
        # Restar stats del usuario
        supabase.table('users').update({
            'total_km': supabase.raw(f"total_km - {activity['distance_km']}"),
            'total_points': supabase.raw(f"total_points - {activity['points_earned']}")
        }).eq('id', str(user_id)).execute()
        
        # Restar stats del equipo
        if activity['team_id']:
            supabase.table('teams').update({
                'total_km': supabase.raw(f"total_km - {activity['distance_km']}"),
                'total_points': supabase.raw(f"total_points - {activity['points_earned']}")
            }).eq('id', activity['team_id']).execute()
        
        # TODO: Recalcular control de zonas afectadas
        
        return True


# Instancia global
activity_processor = ActivityProcessor()
