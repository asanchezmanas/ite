# app/services/strava_service.py

import httpx
from typing import Dict, Optional
from datetime import datetime, timedelta
from uuid import UUID
from app.core.config import settings
from app.core.database import supabase
from app.services.activity_processor import activity_processor


class StravaService:
    """Integración con Strava API"""
    
    BASE_URL = "https://www.strava.com/api/v3"
    AUTH_URL = "https://www.strava.com/oauth/authorize"
    TOKEN_URL = "https://www.strava.com/oauth/token"
    
    def get_authorization_url(self, state: str = None) -> str:
        """Generar URL de autorización de Strava"""
        params = {
            'client_id': settings.STRAVA_CLIENT_ID,
            'redirect_uri': settings.STRAVA_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'read,activity:read_all',
            'state': state or ''
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.AUTH_URL}?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """Intercambiar código de autorización por tokens"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    'client_id': settings.STRAVA_CLIENT_ID,
                    'client_secret': settings.STRAVA_CLIENT_SECRET,
                    'code': code,
                    'grant_type': 'authorization_code'
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refrescar access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    'client_id': settings.STRAVA_CLIENT_ID,
                    'client_secret': settings.STRAVA_CLIENT_SECRET,
                    'refresh_token': refresh_token,
                    'grant_type': 'refresh_token'
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def connect_user(self, user_id: UUID, code: str) -> bool:
        """Conectar cuenta de Strava al usuario"""
        try:
            # Obtener tokens
            token_data = await self.exchange_code_for_token(code)
            
            # Guardar en usuario
            expires_at = datetime.fromtimestamp(token_data['expires_at'])
            
            supabase.table('users').update({
                'strava_athlete_id': token_data['athlete']['id'],
                'strava_access_token': token_data['access_token'],
                'strava_refresh_token': token_data['refresh_token'],
                'strava_token_expires_at': expires_at.isoformat()
            }).eq('id', str(user_id)).execute()
            
            return True
        except Exception as e:
            print(f"Error connecting Strava: {e}")
            return False
    
    async def get_valid_token(self, user_id: UUID) -> Optional[str]:
        """Obtener token válido (refrescar si es necesario)"""
        user_response = supabase.table('users')\
            .select('strava_access_token, strava_refresh_token, strava_token_expires_at')\
            .eq('id', str(user_id))\
            .execute()
        
        if not user_response.data:
            return None
        
        user = user_response.data[0]
        
        if not user.get('strava_access_token'):
            return None
        
        # Verificar si expira pronto (menos de 1 hora)
        expires_at = datetime.fromisoformat(user['strava_token_expires_at'])
        if expires_at < datetime.utcnow() + timedelta(hours=1):
            # Refrescar token
            token_data = await self.refresh_access_token(user['strava_refresh_token'])
            
            new_expires_at = datetime.fromtimestamp(token_data['expires_at'])
            
            supabase.table('users').update({
                'strava_access_token': token_data['access_token'],
                'strava_refresh_token': token_data['refresh_token'],
                'strava_token_expires_at': new_expires_at.isoformat()
            }).eq('id', str(user_id)).execute()
            
            return token_data['access_token']
        
        return user['strava_access_token']
    
    async def sync_activities(
        self, 
        user_id: UUID, 
        after: Optional[datetime] = None,
        before: Optional[datetime] = None
    ) -> int:
        """
        Sincronizar actividades de Strava
        Retorna número de actividades sincronizadas
        """
        token = await self.get_valid_token(user_id)
        if not token:
            return 0
        
        # Por defecto, últimos 30 días
        if not after:
            after = datetime.utcnow() - timedelta(days=30)
        
        params = {
            'after': int(after.timestamp())
        }
        
        if before:
            params['before'] = int(before.timestamp())
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/athlete/activities",
                headers={'Authorization': f'Bearer {token}'},
                params=params
            )
            response.raise_for_status()
            activities = response.json()
        
        synced_count = 0
        
        for strava_activity in activities:
            # Verificar si ya existe
            existing = supabase.table('activities')\
                .select('id')\
                .eq('source', 'strava')\
                .eq('external_id', str(strava_activity['id']))\
                .execute()
            
            if existing.data:
                continue
            
            # Crear actividad
            try:
                await activity_processor.create_activity(
                    user_id=user_id,
                    activity_type=self._map_strava_type(strava_activity['type']),
                    distance_km=strava_activity['distance'] / 1000,
                    duration_minutes=strava_activity['moving_time'] // 60,
                    recorded_at=datetime.fromisoformat(strava_activity['start_date_local'].replace('Z', '+00:00')),
                    polyline=strava_activity['map'].get('summary_polyline'),
                    start_lat=strava_activity.get('start_latlng', [None])[0],
                    start_lng=strava_activity.get('start_latlng', [None, None])[1],
                    avg_pace=self._calculate_pace(strava_activity['distance'], strava_activity['moving_time']),
                    calories=strava_activity.get('calories'),
                    elevation_gain=strava_activity.get('total_elevation_gain'),
                    source='strava',
                    external_id=str(strava_activity['id'])
                )
                synced_count += 1
            except Exception as e:
                print(f"Error syncing activity {strava_activity['id']}: {e}")
                continue
        
        return synced_count
    
    async def handle_webhook(self, webhook_data: Dict) -> bool:
        """
        Manejar webhook de Strava
        Se llama cuando hay una nueva actividad
        """
        aspect_type = webhook_data.get('aspect_type')
        object_type = webhook_data.get('object_type')
        
        if object_type != 'activity':
            return False
        
        if aspect_type == 'create':
            # Nueva actividad creada
            athlete_id = webhook_data.get('owner_id')
            activity_id = webhook_data.get('object_id')
            
            # Buscar usuario por athlete_id
            user_response = supabase.table('users')\
                .select('id')\
                .eq('strava_athlete_id', athlete_id)\
                .execute()
            
            if not user_response.data:
                return False
            
            user_id = user_response.data[0]['id']
            
            # Obtener detalles de la actividad
            token = await self.get_valid_token(user_id)
            if not token:
                return False
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/activities/{activity_id}",
                    headers={'Authorization': f'Bearer {token}'}
                )
                response.raise_for_status()
                strava_activity = response.json()
            
            # Crear actividad
            await activity_processor.create_activity(
                user_id=user_id,
                activity_type=self._map_strava_type(strava_activity['type']),
                distance_km=strava_activity['distance'] / 1000,
                duration_minutes=strava_activity['moving_time'] // 60,
                recorded_at=datetime.fromisoformat(strava_activity['start_date_local'].replace('Z', '+00:00')),
                polyline=strava_activity['map'].get('summary_polyline'),
                start_lat=strava_activity.get('start_latlng', [None])[0],
                start_lng=strava_activity.get('start_latlng', [None, None])[1],
                avg_pace=self._calculate_pace(strava_activity['distance'], strava_activity['moving_time']),
                calories=strava_activity.get('calories'),
                elevation_gain=strava_activity.get('total_elevation_gain'),
                source='strava',
                external_id=str(strava_activity['id'])
            )
            
            return True
        
        elif aspect_type == 'delete':
            # Actividad eliminada
            activity_id = webhook_data.get('object_id')
            
            # Buscar y eliminar actividad
            activity_response = supabase.table('activities')\
                .select('id, user_id')\
                .eq('source', 'strava')\
                .eq('external_id', str(activity_id))\
                .execute()
            
            if activity_response.data:
                activity = activity_response.data[0]
                await activity_processor.delete_activity(activity['id'], activity['user_id'])
            
            return True
        
        return False
    
    @staticmethod
    def _map_strava_type(strava_type: str) -> str:
        """Mapear tipo de actividad de Strava a nuestro sistema"""
        mapping = {
            'Run': 'run',
            'Walk': 'walk',
            'Ride': 'bike',
            'VirtualRun': 'gym',
            'VirtualRide': 'gym'
        }
        return mapping.get(strava_type, 'run')
    
    @staticmethod
    def _calculate_pace(distance_m: float, time_s: int) -> Optional[float]:
        """Calcular pace en min/km"""
        if distance_m == 0:
            return None
        
        km = distance_m / 1000
        minutes = time_s / 60
        return round(minutes / km, 2)


# Instancia global
strava_service = StravaService()
