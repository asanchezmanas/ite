# app/services/competition_service.py

from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime
from app.core.database import supabase
from app.models.competition import ActivityAllocation


class CompetitionService:
    """Gestión de competiciones multi-escala"""
    
    async def allocate_activity_km(
        self,
        activity_id: UUID,
        user_id: UUID,
        allocations: List[ActivityAllocation],
        total_activity_km: float
    ) -> Dict:
        """
        Distribuir KM de una actividad entre competiciones
        Ejemplo: 5km corridos -> 2km para Barcelona, 3km para Badalona
        """
        
        # Validar que las asignaciones no excedan el total
        total_allocated = sum(a.allocated_km for a in allocations)
        
        if total_allocated > total_activity_km:
            raise ValueError(f"Cannot allocate {total_allocated}km from {total_activity_km}km activity")
        
        results = []
        
        for allocation in allocations:
            # Verificar que la competición existe y está activa
            comp_response = supabase.table('competitions')\
                .select('*')\
                .eq('id', str(allocation.competition_id))\
                .eq('status', 'active')\
                .execute()
            
            if not comp_response.data:
                continue
            
            competition = comp_response.data[0]
            
            # Calcular puntos para esta asignación
            points = int(allocation.allocated_km * 10)  # Base points
            
            # Calcular porcentaje si no se proveyó
            percentage = allocation.allocated_percentage or (
                (allocation.allocated_km / total_activity_km) * 100
            )
            
            # Crear asignación
            allocation_data = {
                'activity_id': str(activity_id),
                'competition_id': str(allocation.competition_id),
                'allocated_km': allocation.allocated_km,
                'allocated_percentage': round(percentage, 2),
                'points_earned': points
            }
            
            supabase.table('activity_allocations').insert(allocation_data).execute()
            
            # Verificar si el usuario ya es participante
            participant_response = supabase.table('competition_participants')\
                .select('id')\
                .eq('competition_id', str(allocation.competition_id))\
                .eq('participant_type', 'user')\
                .eq('participant_id', str(user_id))\
                .execute()
            
            if not participant_response.data:
                # Añadir como participante
                await self._add_participant(
                    competition_id=allocation.competition_id,
                    participant_type='user',
                    participant_id=user_id
                )
            
            results.append({
                'competition_id': str(allocation.competition_id),
                'competition_name': competition['name'],
                'allocated_km': allocation.allocated_km,
                'points_earned': points,
                'percentage': round(percentage, 2)
            })
        
        # Recalcular rankings
        await self._recalculate_competition_rankings(allocation.competition_id)
        
        return {
            'total_allocated': total_allocated,
            'remaining_km': total_activity_km - total_allocated,
            'allocations': results
        }
    
    async def _add_participant(
        self,
        competition_id: UUID,
        participant_type: str,
        participant_id: Optional[UUID] = None,
        participant_name: Optional[str] = None
    ):
        """Añadir participante a competición"""
        
        participant_data = {
            'competition_id': str(competition_id),
            'participant_type': participant_type,
            'participant_id': str(participant_id) if participant_id else None,
            'participant_name': participant_name
        }
        
        supabase.table('competition_participants').insert(participant_data).execute()
    
    async def _recalculate_competition_rankings(self, competition_id: UUID):
        """Recalcular rankings de una competición"""
        
        # Obtener todos los participantes ordenados por puntos
        participants = supabase.table('competition_participants')\
            .select('*')\
            .eq('competition_id', str(competition_id))\
            .order('total_points', desc=True)\
            .execute()
        
        # Actualizar ranks
        for idx, participant in enumerate(participants.data, 1):
            supabase.table('competition_participants')\
                .update({'current_rank': idx})\
                .eq('id', participant['id'])\
                .execute()
    
    async def get_active_competitions_for_user(
        self,
        user_id: UUID,
        user_city: Optional[str] = None
    ) -> List[Dict]:
        """
        Obtener competiciones activas relevantes para el usuario
        Incluye: globales, de su ciudad, de su país, de su equipo
        """
        
        # Obtener equipo del usuario
        user_response = supabase.table('users')\
            .select('team_id')\
            .eq('id', str(user_id))\
            .execute()
        
        team_id = user_response.data[0].get('team_id') if user_response.data else None
        
        # Competiciones activas
        competitions_response = supabase.table('competitions')\
            .select('*')\
            .eq('status', 'active')\
            .execute()
        
        relevant_competitions = []
        
        for comp in competitions_response.data:
            # Filtrar por tipo de participante
            is_relevant = False
            
            if comp['participant_type'] == 'individual':
                is_relevant = True
            elif comp['participant_type'] == 'team' and team_id:
                is_relevant = True
            elif comp['participant_type'] == 'city' and user_city:
                is_relevant = comp.get('target_entity') == user_city
            elif comp['participant_type'] == 'country':
                is_relevant = True
            
            if is_relevant:
                # Obtener si ya participa
                participant_check = supabase.table('competition_participants')\
                    .select('*')\
                    .eq('competition_id', comp['id'])\
                    .eq('participant_type', 'user')\
                    .eq('participant_id', str(user_id))\
                    .execute()
                
                comp['is_participating'] = bool(participant_check.data)
                comp['user_stats'] = participant_check.data[0] if participant_check.data else None
                
                relevant_competitions.append(comp)
        
        return relevant_competitions
    
    async def get_competition_leaderboard(
        self,
        competition_id: UUID,
        limit: int = 50
    ) -> List[Dict]:
        """Obtener ranking de una competición"""
        
        participants = supabase.table('competition_participants')\
            .select('*')\
            .eq('competition_id', str(competition_id))\
            .order('current_rank')\
            .limit(limit)\
            .execute()
        
        # Enriquecer con datos de usuario/equipo
        leaderboard = []
        for participant in participants.data:
            entry = dict(participant)
            
            if participant['participant_type'] == 'user' and participant['participant_id']:
                user_data = supabase.table('users')\
                    .select('username, avatar_url')\
                    .eq('id', participant['participant_id'])\
                    .execute()
                
                if user_data.data:
                    entry['user'] = user_data.data[0]
            
            elif participant['participant_type'] == 'team' and participant['participant_id']:
                team_data = supabase.table('teams')\
                    .select('name, color, logo_url')\
                    .eq('id', participant['participant_id'])\
                    .execute()
                
                if team_data.data:
                    entry['team'] = team_data.data[0]
            
            leaderboard.append(entry)
        
        return leaderboard
    
    async def update_geographic_stats(
        self,
        user_id: UUID,
        activity_km: float,
        activity_points: int,
        zone_ids: List[UUID]
    ):
        """
        Actualizar stats del usuario en entidades geográficas
        Basado en las zonas por las que corrió
        """
        
        if not zone_ids:
            return
        
        # Obtener entidades geográficas de las zonas
        zones_response = supabase.table('zones')\
            .select('city_id, region_id, country_id')\
            .in_('id', [str(z) for z in zone_ids])\
            .execute()
        
        # Recopilar todas las entidades únicas
        entity_ids = set()
        for zone in zones_response.data:
            if zone.get('city_id'):
                entity_ids.add(zone['city_id'])
            if zone.get('region_id'):
                entity_ids.add(zone['region_id'])
            if zone.get('country_id'):
                entity_ids.add(zone['country_id'])
        
        # Distribuir KM proporcionalmente entre entidades
        km_per_entity = activity_km / len(entity_ids) if entity_ids else 0
        points_per_entity = activity_points // len(entity_ids) if entity_ids else 0
        
        for entity_id in entity_ids:
            # Upsert stats del usuario en esta entidad
            existing = supabase.table('user_geographic_stats')\
                .select('id')\
                .eq('user_id', str(user_id))\
                .eq('entity_id', entity_id)\
                .execute()
            
            if existing.data:
                # Update
                supabase.table('user_geographic_stats').update({
                    'total_km': supabase.raw(f'total_km + {km_per_entity}'),
                    'total_points': supabase.raw(f'total_points + {points_per_entity}'),
                    'activities_count': supabase.raw('activities_count + 1'),
                    'last_activity_at': datetime.utcnow().isoformat()
                }).eq('id', existing.data[0]['id']).execute()
            else:
                # Insert
                supabase.table('user_geographic_stats').insert({
                    'user_id': str(user_id),
                    'entity_id': entity_id,
                    'total_km': km_per_entity,
                    'total_points': points_per_entity,
                    'activities_count': 1,
                    'last_activity_at': datetime.utcnow().isoformat()
                }).execute()
            
            # Actualizar totales de la entidad
            supabase.table('geographic_entities').update({
                'total_km': supabase.raw(f'total_km + {km_per_entity}')
            }).eq('id', entity_id).execute()
    
    async def get_city_battle(self, city1: str, city2: str) -> Dict:
        """Obtener estado de batalla entre dos ciudades"""
        
        city1_data = supabase.table('geographic_entities')\
            .select('*')\
            .eq('name', city1)\
            .eq('entity_type', 'city')\
            .execute()
        
        city2_data = supabase.table('geographic_entities')\
            .select('*')\
            .eq('name', city2)\
            .eq('entity_type', 'city')\
            .execute()
        
        if not city1_data.data or not city2_data.data:
            return None
        
        c1 = city1_data.data[0]
        c2 = city2_data.data[0]
        
        total_km = c1['total_km'] + c2['total_km']
        
        return {
            'city1': {
                'name': c1['name'],
                'total_km': c1['total_km'],
                'total_users': c1['total_users'],
                'percentage': (c1['total_km'] / total_km * 100) if total_km > 0 else 0
            },
            'city2': {
                'name': c2['name'],
                'total_km': c2['total_km'],
                'total_users': c2['total_users'],
                'percentage': (c2['total_km'] / total_km * 100) if total_km > 0 else 0
            },
            'winner': c1['name'] if c1['total_km'] > c2['total_km'] else c2['name'],
            'is_close': abs(c1['total_km'] - c2['total_km']) < (total_km * 0.05)  # <5% diferencia
        }


# Instancia global
competition_service = CompetitionService()
