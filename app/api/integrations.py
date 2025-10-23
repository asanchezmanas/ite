# app/api/integrations.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from app.api.deps import get_current_user
from app.services.strava_service import strava_service
from app.core.config import settings

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/strava/authorize")
async def strava_authorize(current_user: dict = Depends(get_current_user)):
    """Obtener URL de autorización de Strava"""
    
    # Usar user_id como state para validar callback
    auth_url = strava_service.get_authorization_url(state=current_user['id'])
    
    return {
        "authorization_url": auth_url,
        "message": "Redirect user to this URL to authorize Strava"
    }


@router.get("/strava/callback")
async def strava_callback(
    code: str = Query(...),
    state: str = Query(None),
    scope: str = Query(None)
):
    """
    Callback de Strava después de autorización
    El frontend debe redirigir aquí
    """
    
    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing state parameter"
        )
    
    # Conectar usuario
    success = await strava_service.connect_user(user_id=state, code=code)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to connect Strava account"
        )
    
    # Sincronizar actividades iniciales
    synced = await strava_service.sync_activities(user_id=state)
    
    return {
        "message": "Strava connected successfully",
        "activities_synced": synced
    }


@router.post("/strava/sync")
async def sync_strava_activities(
    current_user: dict = Depends(get_current_user)
):
    """Sincronizar actividades de Strava manualmente"""
    
    if not current_user.get('strava_athlete_id'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Strava not connected"
        )
    
    synced = await strava_service.sync_activities(user_id=current_user['id'])
    
    return {
        "message": "Activities synced successfully",
        "activities_synced": synced
    }


@router.delete("/strava/disconnect")
async def disconnect_strava(current_user: dict = Depends(get_current_user)):
    """Desconectar cuenta de Strava"""
    
    from app.core.database import supabase
    
    supabase.table('users').update({
        'strava_athlete_id': None,
        'strava_access_token': None,
        'strava_refresh_token': None,
        'strava_token_expires_at': None
    }).eq('id', current_user['id']).execute()
    
    return {"message": "Strava disconnected successfully"}


@router.post("/strava/webhook")
async def strava_webhook(request: Request):
    """
    Webhook de Strava para sincronización automática
    
    Para configurar en Strava:
    1. Ir a https://www.strava.com/settings/api
    2. Crear webhook subscription
    3. Callback URL: https://tudominio.com/api/integrations/strava/webhook
    4. Verify Token: usar STRAVA_VERIFY_TOKEN del .env
    """
    
    # Verificación del webhook (GET request)
    if request.method == "GET":
        params = dict(request.query_params)
        
        if params.get('hub.verify_token') != settings.STRAVA_VERIFY_TOKEN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        
        return {"hub.challenge": params.get('hub.challenge')}
    
    # Evento del webhook (POST request)
    data = await request.json()
    
    # Procesar webhook
    await strava_service.handle_webhook(data)
    
    return {"message": "Webhook processed"}


@router.get("/strava/status")
async def strava_status(current_user: dict = Depends(get_current_user)):
    """Verificar estado de conexión con Strava"""
    
    if not current_user.get('strava_athlete_id'):
        return {
            "connected": False,
            "athlete_id": None
        }
    
    return {
        "connected": True,
        "athlete_id": current_user['strava_athlete_id'],
        "token_expires_at": current_user.get('strava_token_expires_at')
    }
