# app/models/competition.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID
from enum import Enum


class CompetitionScope(str, Enum):
    ZONE = "zone"
    DISTRICT = "district"
    CITY = "city"
    REGION = "region"
    COUNTRY = "country"
    GLOBAL = "global"


class CompetitionStatus(str, Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    FINISHED = "finished"


class ParticipantType(str, Enum):
    INDIVIDUAL = "individual"
    TEAM = "team"
    CITY = "city"
    COUNTRY = "country"


class CompetitionBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    scope: CompetitionScope
    target_entity: Optional[str] = None
    participant_type: ParticipantType = ParticipantType.INDIVIDUAL
    min_participants: int = Field(default=2, ge=2)
    max_participants: Optional[int] = None
    start_date: datetime
    end_date: datetime
    prize_pool: float = Field(default=0, ge=0)
    has_achievements: bool = True
    image_url: Optional[str] = None
    rules: Optional[Dict] = None


class CompetitionCreate(CompetitionBase):
    pass


class Competition(CompetitionBase):
    id: UUID
    status: CompetitionStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CompetitionWithStats(Competition):
    """Competición con estadísticas"""
    participant_count: int = 0
    total_km_competition: float = 0
    total_activities: int = 0
    top_participants: List[dict] = []


class CompetitionParticipant(BaseModel):
    id: UUID
    competition_id: UUID
    participant_type: ParticipantType
    participant_id: Optional[UUID] = None
    participant_name: Optional[str] = None
    total_km: float = 0
    total_points: int = 0
    activities_count: int = 0
    current_rank: Optional[int] = None
    joined_at: datetime
    
    class Config:
        from_attributes = True


class ActivityAllocation(BaseModel):
    """Asignación de KM a una competición"""
    competition_id: UUID
    allocated_km: float = Field(..., gt=0)
    allocated_percentage: Optional[float] = Field(None, ge=0, le=100)


class ActivityAllocationRequest(BaseModel):
    """Request para distribuir KM de una actividad"""
    activity_id: UUID
    allocations: List[ActivityAllocation]
    
    def validate_total_percentage(self):
        """Verificar que sume 100%"""
        total = sum(a.allocated_percentage or 0 for a in self.allocations)
        return abs(total - 100) < 0.01


class GeographicEntity(BaseModel):
    """Ciudad, región o país"""
    id: UUID
    name: str
    entity_type: CompetitionScope
    parent_id: Optional[UUID] = None
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    total_zones: int = 0
    total_users: int = 0
    total_teams: int = 0
    total_km: float = 0
    controlled_by_team: Optional[UUID] = None
    controlled_by_city: Optional[str] = None
    controlled_by_country: Optional[str] = None
    control_percentage: float = 0
    flag_emoji: Optional[str] = None
    color: str = "#3B82F6"
    
    class Config:
        from_attributes = True


class UserGeographicStats(BaseModel):
    """Stats de usuario en una entidad geográfica"""
    user_id: UUID
    entity_id: UUID
    entity_name: str
    total_km: float
    total_points: int
    activities_count: int
    rank_in_entity: Optional[int] = None
    
    class Config:
        from_attributes = True
