# app/core/config.py

from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    # API
    PROJECT_NAME: str = "Territory Conquest"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 días
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Strava
    STRAVA_CLIENT_ID: str = ""
    STRAVA_CLIENT_SECRET: str = ""
    STRAVA_REDIRECT_URI: str = "http://localhost:8000/api/integrations/strava/callback"
    STRAVA_VERIFY_TOKEN: str = secrets.token_urlsafe(32)
    
    # H3 Config
    DEFAULT_H3_RESOLUTION: int = 9  # ~0.1 km² por hexágono
    # Resoluciones H3:
    # 8 = ~0.7 km² (barrios pequeños)
    # 9 = ~0.1 km² (manzanas) - RECOMENDADO
    # 10 = ~0.015 km² (muy granular)
    
    # Game Config
    ZONE_CONTROL_THRESHOLD_KM: float = 5.0  # Km mínimos para control inicial
    ZONE_DEFENSE_MULTIPLIER: float = 1.2  # 20% más fácil defender que atacar
    ACTIVITY_POINTS_PER_KM: int = 10
    TEAM_ACTIVITY_BONUS: float = 1.1  # 10% bonus en equipo
    
    # Gym activities
    GYM_ACTIVITY_MULTIPLIER: float = 0.8  # Penalización 20% para gym
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
