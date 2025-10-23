# app/services/risk_service.py

from typing import Dict, List, Optional
from uuid import UUID
from app.core.database import supabase


class RiskConquestService:
    """Servicio para mecánicas estilo RISK"""
    
    async def get_world_map(self, zoom_level: str = 'world') -> Dict:
        """
        Obtener mapa mundial estilo RISK
        zoom_level: world, continent, country, region, city
        """
        
        level_map = {
            'world': 'country',
            'continent': 'country',
            'country': 'region',
            'region': 'city',
            'city': 'district'
        }
        
        entity_type = level_map.get(zoom_level, 'country')
        
        response = supabase.table('v_risk_world_map')\
            .select('*')\
            .eq('territory_type', entity_type)\
            .execute()
        
        territories = []
        for territory in response.data:
            territories.append({
                'id': territory['territory_id'],
                'name': territory['territory_name'],
                'type': territory['territory_type'],
                'position': {
                    'lat': territory['center_lat'],
                    'lng': territory['center_lng']
                },
                'controller': {
                    'name': territory['controller_name'],
                    'flag': territory['controller_flag'],
                    'color': territory['controller_color']
                },
                'units': territory['units'],
                'is_under_attack': territory['is_under_attack'],
                'days_controlled': territory['days_controlled'],
                'battle_progress': territory['battle_progress'],
                'icon': territory['icon'],
                'hexagons': territory['h3_indexes'],
                'special_type': territory['special_type'],
                'defense_bonus': territory['defense_bonus']
            })
        
        return {
            'zoom_level': zoom_level,
            'territories': territories,
            'total': len(territories)
        }
    
    async def get_territory_detail(self, territory_id: UUID) -> Dict:
        """Obtener detalles completos de un territorio"""
        
        # Info básica
        territory_response = supabase.table('geographic_entities')\
            .select('*')\
            .eq('id', str(territory_id))\
            .execute()
        
        if not territory_response.data:
            return None
        
        territory = territory_response.data[0]
        
        # Control actual
        control_response = supabase.table('territory_control')\
            .select('*')\
            .eq('territory_id', str(territory_id))\
            .execute()
        
        control = control_response.data[0] if control_response.data else {}
        
        # Batalla activa
        battle_response = supabase.table('active_battles')\
            .select('*')\
            .eq('territory_id', str(territory_id))\
            .execute()
        
        battle = battle_response.data[0] if battle_response.data else None
        
        # Hexágonos
        hexagon_stats = await self._get_hexagon_distribution(territory_id)
        
        # Territorios conectados
        connected = await self._get_connected_territories(territory_id)
        
        return {
            'territory': territory,
            'control': control,
            'battle': battle,
            'hexagon_distribution': hexagon_stats,
            'connected_territories': connected,
            'strategic_value': self._calculate_strategic_value(territory, connected)
        }
    
    async def _get_hexagon_distribution(self, territory_id: UUID) -> Dict:
        """Obtener distribución de hexágonos por controlador"""
        
        query = """
        SELECT 
            controlled_by_team,
            teams.name as team_name,
            teams.color,
            COUNT(*) as hexagon_count
        FROM zones
        LEFT JOIN teams ON zones.controlled_by_team = teams.id
        WHERE city_id = %s OR region_id = %s OR country_id = %s
        GROUP BY controlled_by_team, teams.name, teams.color
        """
        
        # Nota: Supabase no soporta raw SQL directamente, usar RPC o simplificar
        response = supabase.table('zones')\
            .select('controlled_by_team, city_id, region_id, country_id')\
            .execute()
        
        # Filtrar y agrupar en Python
        hexagons = [z for z in response.data if 
                   z.get('city_id') == str(territory_id) or 
                   z.get('region_id') == str(territory_id) or 
                   z.get('country_id') == str(territory_id)]
        
        distribution = {}
        for hex in hexagons:
            controller = hex.get('controlled_by_team', 'neutral')
            distribution[controller] = distribution.get(controller, 0) + 1
        
        total = len(hexagons)
        
        return {
            'total_hexagons': total,
            'distribution': [
                {
                    'controller': k,
                    'hexagons': v,
                    'percentage': round((v / total * 100), 2) if total > 0 else 0
                }
                for k, v in distribution.items()
            ]
        }
    
    async def _get_connected_territories(self, territory_id: UUID) -> List[Dict]:
        """Obtener territorios conectados (para bonus de cadena)"""
        
        # Obtener el territorio
        territory_response = supabase.table('geographic_entities')\
            .select('connected_territories, parent_id')\
            .eq('id', str(territory_id))\
            .execute()
        
        if not territory_response.data:
            return []
        
        connected_ids = territory_response.data[0].get('connected_territories', [])
        
        if not connected_ids:
            return []
        
        # Obtener info de territorios conectados
        connected_response = supabase.table('geographic_entities')\
            .select('id, name, entity_type')\
            .in_('id', connected_ids)\
            .execute()
        
        return connected_response.data
    
    def _calculate_strategic_value(self, territory: Dict, connected: List) -> int:
        """Calcular valor estratégico del territorio"""
        
        value = 10  # Base
        
        # Bonus por tipo
        if territory.get('is_capital'):
            value += 20
        if territory.get('territory_type') == 'fortress':
            value += 15
        if territory.get('territory_type') == 'strategic_point':
            value += 10
        
        # Bonus por conexiones
        value += len(connected) * 2
        
        # Bonus por producción
        value += territory.get('production_rate', 0) * 5
        
        return value
    
    async def execute_tactical_move(
        self,
        user_id: UUID,
        activity_id: UUID,
        move_type: str,
        from_territory_id: Optional[UUID],
        to_territory_id: UUID,
        units: int,
        km: float
    ) -> Dict:
        """
        Ejecutar movimiento táctico
        move_type: attack, defend, reinforce, transfer
        """
        
        # Llamar a función SQL
        result = supabase.rpc('register_tactical_move', {
            'p_user_id': str(user_id),
            'p_activity_id': str(activity_id),
            'p_move_type': move_type,
            'p_from_territory_id': str(from_territory_id) if from_territory_id else None,
            'p_to_territory_id': str(to_territory_id),
            'p_units': units,
            'p_km': km
        }).execute()
        
        return result.data if result.data else {}
    
    async def get_active_battles(self, user_related: bool = False, user_id: UUID = None) -> List[Dict]:
        """Obtener batallas activas"""
        
        query = supabase.table('v_active_battles_detail').select('*')
        
        if user_related and user_id:
            # Obtener territorios relacionados con el usuario
            # (su ciudad, región, país, o equipo)
            pass  # Implementar filtro
        
        response = query.limit(50).execute()
        
        return response.data
    
    async def get_battle_detail(self, battle_id: UUID) -> Dict:
        """Obtener detalles de una batalla específica"""
        
        battle_response = supabase.table('active_battles')\
            .select('*')\
            .eq('id', str(battle_id))\
            .execute()
        
        if not battle_response.data:
            return None
        
        battle = battle_response.data[0]
        
        # Últimos movimientos en esta batalla
        moves_response = supabase.table('tactical_moves')\
            .select('*, users(username, avatar_url)')\
            .eq('to_territory_id', battle['territory_id'])\
            .order('created_at', desc=True)\
            .limit(20)\
            .execute()
        
        # Participantes
        participants_response = supabase.rpc('get_battle_participants', {
            'p_battle_id': str(battle_id)
        }).execute()
        
        return {
            'battle': battle,
            'recent_moves': moves_response.data,
            'participants': participants_response.data if participants_response.data else [],
            'hexagon_map': await self._get_battle_hexagon_map(battle['territory_id'])
        }
    
    async def _get_battle_hexagon_map(self, territory_id: UUID) -> List[Dict]:
        """Obtener mapa de hexágonos en batalla"""
        
        response = supabase.table('entity_hexagon_control')\
            .select('*')\
            .eq('entity_id', str(territory_id))\
            .eq('is_contested', True)\
            .execute()
        
        hexagons = []
        for hex_data in response.data:
            hexagons.append({
                'h3_index': hex_data['h3_index'],
                'controller': hex_data['controlling_team'],
                'strength': hex_data['control_strength'],
                'contested_by': hex_data['contested_by_entity'],
                'recent_activity': hex_data['recent_km']
            })
        
        return hexagons
    
    async def get_territorial_rankings(self, scope: str = 'global') -> List[Dict]:
        """
        Obtener rankings territoriales
        scope: global, continent, country, region
        """
        
        response = supabase.table('v_territorial_rankings')\
            .select('*')\
            .execute()
        
        return response.data
    
    async def get_hot_borders(self, limit: int = 10) -> List[Dict]:
        """Obtener fronteras más activas"""
        
        response = supabase.table('v_hot_borders')\
            .select('*')\
            .limit(limit)\
            .execute()
        
        return response.data
    
    async def get_conquest_history(
        self,
        territory_id: Optional[UUID] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Obtener historial de conquistas"""
        
        query = supabase.table('conquest_history').select('*')
        
        if territory_id:
            query = query.eq('territory_id', str(territory_id))
        
        response = query.order('conquered_at', desc=True).limit(limit).execute()
        
        return response.data
    
    async def get_user_impact_summary(self, user_id: UUID) -> Dict:
        """Resumen del impacto del usuario en el mapa"""
        
        # Movimientos del usuario
        moves_response = supabase.table('tactical_moves')\
            .select('*')\
            .eq('user_id', str(user_id))\
            .execute()
        
        total_moves = len(moves_response.data)
        critical_moves = len([m for m in moves_response.data if m.get('was_critical')])
        conquests_participated = len([m for m in moves_response.data if m.get('turned_tide')])
        
        # Territorios donde ha contribuido
        territories = set([m['to_territory_id'] for m in moves_response.data])
        
        # Impacto total
        total_units = sum([m.get('units_moved', 0) for m in moves_response.data])
        total_km = sum([m.get('km_allocated', 0) for m in moves_response.data])
        
        return {
            'total_moves': total_moves,
            'critical_moves': critical_moves,
            'conquests_participated': conquests_participated,
            'territories_impacted': len(territories),
            'total_units_deployed': total_units,
            'total_km_allocated': float(total_km),
            'average_impact_per_move': total_units / total_moves if total_moves > 0 else 0
        }
    
    async def suggest_strategic_targets(self, user_id: UUID, user_city: str) -> List[Dict]:
        """Sugerir objetivos estratégicos para el usuario"""
        
        suggestions = []
        
        # 1. Fronteras en peligro
        hot_borders = await self.get_hot_borders(limit=5)
        for border in hot_borders:
            if user_city in [border['entity_1_name'], border['entity_2_name']]:
                suggestions.append({
                    'type': 'defend_border',
                    'priority': 'HIGH',
                    'target': border,
                    'reason': f"Frontera con {border['entity_2_name']} en disputa",
                    'recommended_units': 10
                })
        
        # 2. Batallas activas cercanas
        battles = await self.get_active_battles(user_related=True, user_id=user_id)
        for battle in battles[:3]:
            if battle['conquest_progress'] > 50:
                suggestions.append({
                    'type': 'defend_territory',
                    'priority': 'CRITICAL',
                    'target': battle,
                    'reason': f"{battle['territory_name']} a punto de caer",
                    'recommended_units': 15
                })
        
        # 3. Territorios débiles enemigos (oportunidades)
        # ... lógica adicional
        
        return suggestions


# Instancia global
risk_service = RiskConquestService()
