# app/models/activity.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class ActivityType(str, Enum):
    RUN = "run"
    WALK = "walk"
    BIKE = "bike"
    GYM = "gym"


class ActivitySource(str, Enum):
    MANUAL = "manual"
    STRAVA = "strava"
    GARMIN = "garmin"


class ActivityBase(BaseModel):
    activity_type: ActivityType = ActivityType.RUN
    distance_km: float = Field(..., gt=0, le=500)
    duration_minutes: Optional[int] = Field(None, gt=0)
    avg_pace: Optional[float] = Field(None, gt=0)
    calories: Optional[int] = Field(None, ge=0)
    elevation_gain: Optional[int] = Field(None, ge=0)
    
    start_lat: Optional[float] = Field(None, ge=-90, le=90)
    start_lng: Optional[float] = Field(None, ge=-180, le=180)
    polyline: Optional[str] = None
    
    recorded_at: datetime


class ActivityCreate(ActivityBase):
    is_gym_activity: bool = False
    assigned_zones: Optional[List[str]] = None  # H3 indexes
    
    @field_validator('assigned_zones')
    @classmethod
    def validate_gym_zones(cls, v, info):
        if info.data.get('is_gym_activity') and not v:
            raise ValueError('Gym activities must have assigned zones')
        if not info.data.get('is_gym_activity') and v:
            raise ValueError('Only gym activities can have assigned zones')
        return v


class Activity(ActivityBase):
    id: UUID
    user_id: UUID
    team_id: Optional[UUID] = None
    is_gym_activity: bool = False
    assigned_zones: Optional[List[str]] = None
    source: ActivitySource = ActivitySource.MANUAL
    external_id: Optional[str] = None
    points_earned: int = 0
    synced_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class ActivityWithZones(Activity):
    """Activity con zonas afectadas"""
    affected_zones: List[dict] = []
