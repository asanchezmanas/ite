# app/api/risk.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID
from app.api.deps import get_current_user
from app.services.risk_service import risk_service
from pydantic import BaseModel

router = APIRouter(prefix="/risk", tags=["risk-conquest"])


class TacticalMoveRequest(BaseModel):
    activity_id: UUID
    move_type: str  # attack, defend, reinforce
    from_territory_id: Optional[UUID] = None
    to_territory_id: UUID
    units: int
    km: float


@router.get("/map")
async def get_risk_map(
    zoom: str = Query('world', regex="^(world|continent|country|region|city)$")
):
    """
    Obtener mapa estilo RISK
    zoom: world, continent, country, region, city
    
    Retorna territorios con:
    - Nombre y posición
    - Controlador (nombre, bandera, color)
    - Unidades (número visible)
    - Estado (bajo ataque, días controlado)
    - Hexágonos
    """
    return await risk_service.get_world_map(zoom_level=zoom)


@router.get("/territory/{territory_id}")
async def get_territory_detail(territory_id: str):
    """
    Detalles completos de un territorio
    
    Incluye:
    - Info del territorio
    - Control actual
    - Batalla activa (si hay)
    - Distribución de hexágonos
    - Territorios conectados
    - Valor estratégico
    """
    territory = await risk_service.get_territory_detail(UUID(territory_id))
    
    if not territory:
        raise HTTPException(status_code=404, detail="Territory not found")
    
    return territory


@router.post("/move")
async def execute_tactical_move(
    move: TacticalMoveRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Ejecutar movimiento táctico
    
    Tipos:
    - attack: Atacar territorio enemigo
    - defend: Reforzar territorio propio
    - reinforce: Mover unidades entre territorios propios
    
    Ejemplo:
    {
      "activity_id": "uuid",
      "move_type": "attack",
      "to_territory_id": "uuid-francia",
      "units": 10,
      "km": 10.0
    }
    """
    
    # Verificar que la actividad existe y pertenece al usuario
    from app.core.database import supabase
    activity = supabase.table('activities')\
        .select('*')\
        .eq('id', str(move.activity_id))\
        .eq('user_id', current_user['id'])\
        .execute()
    
    if not activity.data:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    result = await risk_service.execute_tactical_move(
        user_id=UUID(current_user['id']),
        activity_id=move.activity_id,
        move_type=move.move_type,
        from_territory_id=move.from_territory_id,
        to_territory_id=move.to_territory_id,
        units=move.units,
        km=move.km
    )
    
    return result


@router.get("/battles")
async def get_active_battles(
    user_related: bool = Query(False),
    current_user: dict = Depends(get_current_user)
):
    """
    Listar batallas activas
    
    user_related=true → Solo batallas que afectan al usuario
    """
    
    user_id = UUID(current_user['id']) if user_related else None
    battles = await risk_service.get_active_battles(
        user_related=user_related,
        user_id=user_id
    )
    
    return {
        'total': len(battles),
        'battles': battles
    }


@router.get("/battles/{battle_id}")
async def get_battle_detail(battle_id: str):
    """
    Detalles de una batalla específica
    
    Incluye:
    - Estado de la batalla
    - Últimos 20 movimientos
    - Participantes
    - Mapa de hexágonos en disputa
    """
    
    battle = await risk_service.get_battle_detail(UUID(battle_id))
    
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    
    return battle


@router.get("/rankings")
async def get_territorial_rankings(
    scope: str = Query('global', regex="^(global|continent|country|region)$")
):
    """
    Rankings territoriales
    
    Muestra:
    - Territorios controlados por cada entidad
    - Unidades totales
    - Capitales y fortalezas
    - Territorios bajo ataque
    """
    
    rankings = await risk_service.get_territorial_rankings(scope=scope)
    
    return {
        'scope': scope,
        'rankings': rankings
    }


@router.get("/borders/hot")
async def get_hot_borders(limit: int = Query(10, ge=1, le=50)):
    """
    Fronteras más disputadas
    
    Ordenadas por:
    - Equilibrio de fuerzas (50-50 = más disputada)
    - Número de batallas
    - Actividad reciente
    """
    
    borders = await risk_service.get_hot_borders(limit=limit)
    
    return {
        'total': len(borders),
        'borders': borders
    }


@router.get("/history/conquests")
async def get_conquest_history(
    territory_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """
    Historial de conquistas
    
    territory_id → Conquistas de un territorio específico
    sin territory_id → Todas las conquistas recientes
    """
    
    tid = UUID(territory_id) if territory_id else None
    history = await risk_service.get_conquest_history(
        territory_id=tid,
        limit=limit
    )
    
    return {
        'total': len(history),
        'conquests': history
    }


@router.get("/user/impact")
async def get_user_impact(current_user: dict = Depends(get_current_user)):
    """
    Resumen del impacto del usuario
    
    Stats:
    - Movimientos totales
    - Movimientos críticos
    - Conquistas en las que participó
    - Territorios impactados
    - Unidades desplegadas
    """
    
    impact = await risk_service.get_user_impact_summary(
        user_id=UUID(current_user['id'])
    )
    
    return impact


@router.get("/user/suggestions")
async def get_strategic_suggestions(
    current_user: dict = Depends(get_current_user)
):
    """
    Sugerencias estratégicas personalizadas
    
    Analiza:
    - Fronteras en peligro
    - Batallas críticas
    - Oportunidades de conquista
    - Territorios débiles enemigos
    
    Retorna lista priorizada de objetivos
    """
    
    # TODO: Obtener ciudad del usuario
    user_city = "Barcelona"  # Placeholder
    
    suggestions = await risk_service.suggest_strategic_targets(
        user_id=UUID(current_user['id']),
        user_city=user_city
    )
    
    return {
        'total': len(suggestions),
        'suggestions': suggestions
    }


@router.get("/stats/global")
async def get_global_stats():
    """
    Estadísticas globales del mapa
    
    Retorna:
    - Total de territorios
    - Territorios en disputa
    - Batallas activas
    - Conquistas hoy/semana
    - Top países por territorio
    """
    
    from app.core.database import supabase
    
    # Total territorios
    territories_count = supabase.table('territory_control')\
        .select('id', count='exact')\
        .execute()
    
    # Bajo ataque
    under_attack = supabase.table('territory_control')\
        .select('id', count='exact')\
        .eq('is_under_attack', True)\
        .execute()
    
    # Batallas activas
    battles = supabase.table('active_battles')\
        .select('id', count='exact')\
        .execute()
    
    # Conquistas hoy
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    conquests_today = supabase.table('conquest_history')\
        .select('id', count='exact')\
        .gte('conquered_at', today.isoformat())\
        .execute()
    
    return {
        'total_territories': territories_count.count,
        'territories_under_attack': under_attack.count,
        'active_battles': battles.count,
        'conquests_today': conquests_today.count,
        'conquest_rate': f"{conquests_today.count} per day"
    }


@router.get("/preview/battle/{territory_id}")
async def preview_attack(
    territory_id: str,
    units: int = Query(..., ge=1),
    current_user: dict = Depends(get_current_user)
):
    """
    Previsualizar resultado de ataque
    
    Simula qué pasaría si atacas con X unidades
    Sin ejecutar el movimiento
    
    Retorna:
    - Probabilidad de éxito
    - Hexágonos que conquistarías
    - Progreso hacia conquista total
    - Riesgo de contraataque
    """
    
    territory = await risk_service.get_territory_detail(UUID(territory_id))
    
    if not territory:
        raise HTTPException(status_code=404, detail="Territory not found")
    
    control = territory['control']
    current_defender_units = control.get('units', 0)
    
    # Cálculo simplificado
    attack_strength = units
    defense_strength = current_defender_units * (1 + control.get('defense_bonus', 0))
    
    success_probability = min(100, (attack_strength / defense_strength) * 100) if defense_strength > 0 else 100
    
    hexagon_dist = territory.get('hexagon_distribution', {})
    total_hexagons = hexagon_dist.get('total_hexagons', 0)
    
    # Estimar hexágonos conquistables
    estimated_conquest = int(total_hexagons * (success_probability / 200))
    
    return {
        'territory_name': territory['territory']['name'],
        'current_units': current_defender_units,
        'attack_units': units,
        'defense_bonus': control.get('defense_bonus', 0),
        'success_probability': round(success_probability, 2),
        'estimated_hexagons_conquered': estimated_conquest,
        'progress_to_conquest': round(estimated_conquest / total_hexagons * 100, 2) if total_hexagons > 0 else 0,
        'recommendation': 'GO!' if success_probability > 60 else 'RISKY' if success_probability > 40 else 'AVOID'
    }
