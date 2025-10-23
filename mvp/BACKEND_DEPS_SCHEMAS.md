# 🔌 Backend API Dependencies & Schemas

## 📁 app/api/deps.py

```python
"""
API Dependencies - Reusable dependencies for route handlers
"""

from typing import Optional, Generator
from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import security
from app.core.database import db
from app.core.exceptions import AuthenticationError, UserNotFound
from app.core.logging import get_logger
from pydantic import BaseModel

logger = get_logger(__name__)
security_scheme = HTTPBearer()


# ============================================
# Authentication Dependencies
# ============================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> dict:
    """
    Validate JWT token and return current user
    
    Raises:
        AuthenticationError: If token is invalid or user not found
    """
    token = credentials.credentials
    
    try:
        # Decode token
        payload = security.decode_token(token)
        
        # Validate it's an access token
        security.validate_token_type(payload, "access")
        
        # Get user ID from token
        user_id: str = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Token missing user ID")
        
        # Fetch user from database
        result = db.client.table('users')\
            .select('*')\
            .eq('id', user_id)\
            .eq('is_active', True)\
            .single()\
            .execute()
        
        if not result.data:
            raise UserNotFound(user_id)
        
        logger.debug("User authenticated", user_id=user_id)
        return result.data
        
    except Exception as e:
        logger.warning("Authentication failed", error=str(e))
        raise


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get current user and verify they are active
    """
    if not current_user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    Optional authentication - returns None if no token provided
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except:
        return None


# ============================================
# Pagination Dependencies
# ============================================

class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = 1
    limit: int = 20
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit
    
    @property
    def skip(self) -> int:
        return self.offset


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
) -> PaginationParams:
    """Get pagination parameters from query string"""
    return PaginationParams(page=page, limit=limit)


# ============================================
# Filtering Dependencies
# ============================================

class FilterParams(BaseModel):
    """Common filter parameters"""
    search: Optional[str] = None
    sort_by: Optional[str] = None
    order: str = "desc"  # asc or desc


def get_filter_params(
    search: Optional[str] = Query(None, description="Search term"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
) -> FilterParams:
    """Get filter parameters from query string"""
    return FilterParams(search=search, sort_by=sort_by, order=order)


# ============================================
# Resource Ownership Dependencies
# ============================================

async def verify_team_membership(
    team_id: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Verify user is a member of the specified team
    
    Raises:
        HTTPException: If user is not a member
    """
    if current_user.get('team_id') != team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team"
        )
    
    # Fetch team data
    result = db.client.table('teams')\
        .select('*')\
        .eq('id', team_id)\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    return result.data


async def verify_activity_ownership(
    activity_id: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Verify user owns the specified activity
    
    Raises:
        HTTPException: If user doesn't own the activity
    """
    result = db.client.table('activities')\
        .select('*')\
        .eq('id', activity_id)\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    if result.data['user_id'] != current_user['id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't own this activity"
        )
    
    return result.data


# ============================================
# Rate Limiting Dependency
# ============================================

from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Create rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[] if not settings.RATE_LIMIT_ENABLED else [
        f"{settings.RATE_LIMIT_PER_MINUTE}/minute"
    ]
)


def rate_limit(limit: str):
    """
    Rate limiting decorator
    
    Usage:
        @router.post("/api/activities")
        @rate_limit("10/minute")
        async def create_activity(...):
            pass
    """
    return limiter.limit(limit)
```

---

## 📋 app/schemas/common.py

```python
"""
Common schemas used across the application
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response wrapper"""
    success: bool = True
    data: T
    message: Optional[str] = None
    meta: Optional[dict] = None


class ErrorDetail(BaseModel):
    """Error detail for validation errors"""
    field: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: dict = Field(..., description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response"""
    success: bool = True
    data: List[T]
    meta: dict = Field(..., description="Pagination metadata")
    
    @classmethod
    def create(
        cls,
        data: List[T],
        page: int,
        limit: int,
        total: int
    ):
        """Create paginated response"""
        return cls(
            data=data,
            meta={
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit,
                "has_next": page * limit < total,
                "has_prev": page > 1
            }
        )


class MessageResponse(BaseModel):
    """Simple message response"""
    success: bool = True
    message: str
```

---

## 👤 app/schemas/user.py

```python
"""
User schemas
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password meets strength requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                'Password must contain uppercase, lowercase, and numbers'
            )
        
        return v
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, _ and -')
        return v


class UserUpdate(BaseModel):
    """Schema for user profile update"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    avatar_url: Optional[str] = None
    team_id: Optional[str] = None


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    email: EmailStr
    username: str
    avatar_url: Optional[str] = None
    total_km: float = 0
    total_points: int = 0
    zones_count: int = 0
    team_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserPublicProfile(BaseModel):
    """Public user profile (limited info)"""
    id: str
    username: str
    avatar_url: Optional[str] = None
    total_km: float
    total_points: int
    zones_count: int
    team_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """User statistics"""
    total_activities: int
    total_km: float
    total_points: int
    zones_controlled: int
    team_name: Optional[str] = None
    global_rank: Optional[int] = None
    country_rank: Optional[int] = None
    city_rank: Optional[int] = None
    current_streak_days: int = 0
    best_streak_days: int = 0
```

---

## 🔐 app/schemas/auth.py

```python
"""
Authentication schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from .user import UserResponse


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Full authentication response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Password change request"""
    old_password: str
    new_password: str
```

---

## 🏃 app/schemas/activity.py

```python
"""
Activity schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class ActivityBase(BaseModel):
    """Base activity schema"""
    distance_km: float = Field(..., gt=0, description="Distance in kilometers")
    duration_minutes: int = Field(..., gt=0, description="Duration in minutes")
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lng: float = Field(..., ge=-180, le=180, description="Longitude")
    
    @validator('distance_km')
    def validate_distance(cls, v):
        """Validate distance is reasonable"""
        if v < 0.1:
            raise ValueError('Distance must be at least 0.1 km')
        if v > 500:
            raise ValueError('Distance cannot exceed 500 km')
        return v
    
    @validator('duration_minutes')
    def validate_duration(cls, v):
        """Validate duration is reasonable"""
        if v < 1:
            raise ValueError('Duration must be at least 1 minute')
        if v > 1440:  # 24 hours
            raise ValueError('Duration cannot exceed 24 hours')
        return v


class ActivityCreate(ActivityBase):
    """Schema for activity creation"""
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('recorded_at')
    def validate_recorded_at(cls, v):
        """Validate recorded_at is not in the future"""
        if v > datetime.utcnow():
            raise ValueError('recorded_at cannot be in the future')
        return v


class ActivityUpdate(BaseModel):
    """Schema for activity update"""
    distance_km: Optional[float] = Field(None, gt=0)
    duration_minutes: Optional[int] = Field(None, gt=0)


class ActivityResponse(BaseModel):
    """Activity response schema"""
    id: str
    user_id: str
    team_id: Optional[str] = None
    distance_km: float
    duration_minutes: int
    lat: float
    lng: float
    city: Optional[str] = None
    points_earned: int
    recorded_at: datetime
    created_at: datetime
    
    # Computed fields
    pace_min_per_km: Optional[float] = None
    speed_km_per_h: Optional[float] = None
    
    class Config:
        from_attributes = True
    
    @validator('pace_min_per_km', always=True)
    def calculate_pace(cls, v, values):
        """Calculate pace"""
        if 'duration_minutes' in values and 'distance_km' in values:
            if values['distance_km'] > 0:
                return values['duration_minutes'] / values['distance_km']
        return None
    
    @validator('speed_km_per_h', always=True)
    def calculate_speed(cls, v, values):
        """Calculate speed"""
        if 'duration_minutes' in values and 'distance_km' in values:
            if values['duration_minutes'] > 0:
                return (values['distance_km'] / values['duration_minutes']) * 60
        return None


class ActivityWithZones(ActivityResponse):
    """Activity with affected zones"""
    zones_affected: List[dict] = []


class ActivityListItem(BaseModel):
    """Simplified activity for list views"""
    id: str
    distance_km: float
    duration_minutes: int
    points_earned: int
    recorded_at: datetime
    city: Optional[str] = None
```

---

## 👥 app/schemas/team.py

```python
"""
Team schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from .user import UserPublicProfile


class TeamBase(BaseModel):
    """Base team schema"""
    name: str = Field(..., min_length=3, max_length=100)
    color: str = Field(default="#3B82F6", regex="^#[0-9A-Fa-f]{6}$")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate team name"""
        if not v.strip():
            raise ValueError('Team name cannot be empty')
        return v.strip()


class TeamCreate(TeamBase):
    """Schema for team creation"""
    description: Optional[str] = Field(None, max_length=500)


class TeamUpdate(BaseModel):
    """Schema for team update"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    description: Optional[str] = Field(None, max_length=500)


class TeamResponse(BaseModel):
    """Team response schema"""
    id: str
    name: str
    color: str
    description: Optional[str] = None
    members_count: int
    total_km: float
    total_points: int
    rank: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TeamWithMembers(TeamResponse):
    """Team with member details"""
    members: List[UserPublicProfile] = []


class TeamLeaderboardItem(BaseModel):
    """Team leaderboard item"""
    rank: int
    id: str
    name: str
    color: str
    total_km: float
    total_points: int
    members_count: int
    zones_count: int = 0
```

---

## 🗺️ app/schemas/zone.py

```python
"""
Zone schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ZoneBase(BaseModel):
    """Base zone schema"""
    h3_index: str
    center_lat: float = Field(..., ge=-90, le=90)
    center_lng: float = Field(..., ge=-180, le=180)
    city: str


class ZoneCreate(ZoneBase):
    """Schema for zone creation"""
    pass


class ZoneResponse(BaseModel):
    """Zone response schema"""
    id: str
    h3_index: str
    center_lat: float
    center_lng: float
    city: str
    controlled_by_team: Optional[str] = None
    control_strength: float = 0
    total_km: float = 0
    last_activity_at: Optional[datetime] = None
    created_at: datetime
    
    # Computed fields
    team_name: Optional[str] = None
    team_color: Optional[str] = None
    
    class Config:
        from_attributes = True


class ZoneBoundary(BaseModel):
    """Zone boundary coordinates"""
    h3_index: str
    boundary: List[dict]  # List of {lat, lng}


class ZoneControl(BaseModel):
    """Zone control information"""
    zone_id: str
    h3_index: str
    controlled_by_team: Optional[str] = None
    team_name: Optional[str] = None
    team_color: Optional[str] = None
    control_strength: float
    total_km: float
```

---

## 🏆 app/schemas/leaderboard.py

```python
"""
Leaderboard schemas
"""

from pydantic import BaseModel
from typing import Optional


class UserLeaderboardItem(BaseModel):
    """User leaderboard item"""
    rank: int
    id: str
    username: str
    avatar_url: Optional[str] = None
    total_km: float
    total_points: int
    zones_count: int
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    team_color: Optional[str] = None


class TeamLeaderboardItem(BaseModel):
    """Team leaderboard item"""
    rank: int
    id: str
    name: str
    color: str
    total_km: float
    total_points: int
    members_count: int
    zones_count: int = 0
```

---

Continúo con los routers (endpoints completos) en el próximo archivo.
