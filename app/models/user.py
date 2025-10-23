# app/models/user.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    team_id: Optional[UUID] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: UUID
    avatar_url: Optional[str] = None
    total_km: float = 0
    total_points: int = 0
    zones_controlled: int = 0
    team_id: Optional[UUID] = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserPublic(BaseModel):
    """Datos públicos del usuario"""
    id: UUID
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    total_km: float
    total_points: int
    zones_controlled: int
    team_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None  # user_id
