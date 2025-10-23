# 🚀 Backend API Routers & Main Application

## 📁 app/main.py

```python
"""
Main FastAPI application with all configurations
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import TerritoryException
from app.core.database import db

# Import routers
from app.api import auth, users, activities, teams, zones, leaderboard, stats

# Setup logging
setup_logging()
logger = get_logger(__name__)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting Territory Conquest API", version=settings.APP_VERSION)
    
    # Check database connection
    if db.health_check():
        logger.info("✅ Database connection healthy")
    else:
        logger.error("❌ Database connection failed")
    
    # Initialize Sentry if configured
    if settings.SENTRY_DSN:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        )
        logger.info("✅ Sentry initialized")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down Territory Conquest API")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Territory conquest through sports - MVP API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)


# ============================================
# Middleware
# ============================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    logger.info(
        "Request",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else None
    )
    
    response = await call_next(request)
    
    logger.info(
        "Response",
        method=request.method,
        path=request.url.path,
        status=response.status_code
    )
    
    return response


# ============================================
# Exception Handlers
# ============================================

@app.exception_handler(TerritoryException)
async def territory_exception_handler(request: Request, exc: TerritoryException):
    """Handle custom Territory exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.detail
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "message": error["msg"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input",
                "details": errors
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(
        "Unexpected error",
        error=str(exc),
        path=request.url.path,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        }
    )


# ============================================
# Routers
# ============================================

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(activities.router, prefix="/api/activities", tags=["Activities"])
app.include_router(teams.router, prefix="/api/teams", tags=["Teams"])
app.include_router(zones.router, prefix="/api/map", tags=["Map & Zones"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["Leaderboards"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])


# ============================================
# Health & Info Endpoints
# ============================================

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.DEBUG else None
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check"""
    return {"status": "healthy"}


@app.get("/health/db", tags=["Health"])
async def database_health():
    """Database health check"""
    is_healthy = db.health_check()
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "database": "connected" if is_healthy else "disconnected"
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness probe for Kubernetes"""
    db_healthy = db.health_check()
    
    if not db_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready"}
        )
    
    return {"status": "ready"}


@app.get("/health/live", tags=["Health"])
async def liveness_check():
    """Liveness probe for Kubernetes"""
    return {"status": "alive"}
```

---

## 🔐 app/api/auth.py

```python
"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import (
    LoginRequest, AuthResponse, RefreshTokenRequest, TokenResponse
)
from app.schemas.user import UserCreate, UserResponse
from app.core.security import security
from app.core.database import db
from app.core.exceptions import (
    InvalidCredentials, UserAlreadyExists, WeakPassword
)
from app.core.logging import get_logger
from app.api.deps import rate_limit

router = APIRouter()
logger = get_logger(__name__)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@rate_limit("5/hour")  # Prevent spam registrations
async def register(user_data: UserCreate):
    """
    Register a new user
    
    - **email**: Valid email address
    - **username**: 3-50 characters, alphanumeric
    - **password**: Minimum 8 characters, must include uppercase, lowercase, and numbers
    """
    try:
        # Check if email already exists
        existing = db.client.table('users')\
            .select('id')\
            .eq('email', user_data.email)\
            .execute()
        
        if existing.data:
            raise UserAlreadyExists("email", user_data.email)
        
        # Check if username already exists
        existing = db.client.table('users')\
            .select('id')\
            .eq('username', user_data.username)\
            .execute()
        
        if existing.data:
            raise UserAlreadyExists("username", user_data.username)
        
        # Validate password strength
        if not security.validate_password_strength(user_data.password):
            raise WeakPassword()
        
        # Register with Supabase Auth
        auth_response = db.client.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )
        
        # Create user profile
        user_profile = {
            "id": auth_response.user.id,
            "email": user_data.email,
            "username": user_data.username
        }
        
        db.client.table('users').insert(user_profile).execute()
        
        # Create tokens
        access_token = security.create_access_token(subject=auth_response.user.id)
        refresh_token = security.create_refresh_token(subject=auth_response.user.id)
        
        # Fetch complete user profile
        user = db.client.table('users')\
            .select('*')\
            .eq('id', auth_response.user.id)\
            .single()\
            .execute()
        
        logger.info("User registered", user_id=auth_response.user.id, username=user_data.username)
        
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user.data
        )
        
    except (UserAlreadyExists, WeakPassword):
        raise
    except Exception as e:
        logger.error("Registration error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=AuthResponse)
@rate_limit("10/minute")  # Prevent brute force
async def login(credentials: LoginRequest):
    """
    Login with email and password
    
    Returns access token, refresh token, and user profile
    """
    try:
        # Sign in with Supabase
        response = db.client.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if not response.session:
            raise InvalidCredentials()
        
        # Get user profile
        user = db.client.table('users')\
            .select('*')\
            .eq('id', response.user.id)\
            .eq('is_active', True)\
            .single()\
            .execute()
        
        if not user.data:
            raise InvalidCredentials()
        
        # Create our own tokens (not using Supabase's)
        access_token = security.create_access_token(subject=response.user.id)
        refresh_token = security.create_refresh_token(subject=response.user.id)
        
        logger.info("User logged in", user_id=response.user.id)
        
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user.data
        )
        
    except InvalidCredentials:
        raise
    except Exception as e:
        logger.error("Login error", error=str(e))
        raise InvalidCredentials()


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    """
    try:
        # Decode refresh token
        payload = security.decode_token(request.refresh_token)
        
        # Validate it's a refresh token
        security.validate_token_type(payload, "refresh")
        
        user_id = payload.get("sub")
        
        # Verify user still exists and is active
        user = db.client.table('users')\
            .select('id')\
            .eq('id', user_id)\
            .eq('is_active', True)\
            .single()\
            .execute()
        
        if not user.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        new_access_token = security.create_access_token(subject=user_id)
        new_refresh_token = security.create_refresh_token(subject=user_id)
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token
        )
        
    except Exception as e:
        logger.error("Token refresh error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout():
    """
    Logout (client should discard tokens)
    
    In a production environment with Redis, you would:
    1. Add token to blacklist
    2. Delete refresh token from storage
    """
    return {"message": "Logged out successfully"}
```

---

## 👤 app/api/users.py

```python
"""
User endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.schemas.user import UserResponse, UserUpdate, UserPublicProfile, UserStats
from app.schemas.common import MessageResponse
from app.core.database import db
from app.api.deps import get_current_user
from app.core.exceptions import UserNotFound
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current user profile
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update current user profile
    
    Can update:
    - username
    - avatar_url
    - team_id
    """
    try:
        # Prepare update data (only non-None fields)
        data = update_data.dict(exclude_none=True)
        
        if not data:
            return current_user
        
        # If changing username, check if available
        if 'username' in data:
            existing = db.client.table('users')\
                .select('id')\
                .eq('username', data['username'])\
                .neq('id', current_user['id'])\
                .execute()
            
            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already taken"
                )
        
        # Update user
        result = db.client.table('users')\
            .update(data)\
            .eq('id', current_user['id'])\
            .execute()
        
        logger.info("User profile updated", user_id=current_user['id'], fields=list(data.keys()))
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Profile update error", user_id=current_user['id'], error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.get("/me/stats", response_model=UserStats)
async def get_current_user_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current user statistics
    """
    try:
        # Get activity count
        activities = db.client.table('activities')\
            .select('id', count='exact')\
            .eq('user_id', current_user['id'])\
            .execute()
        
        # Get team info if user has a team
        team_name = None
        if current_user.get('team_id'):
            team = db.client.table('teams')\
                .select('name')\
                .eq('id', current_user['team_id'])\
                .single()\
                .execute()
            team_name = team.data['name'] if team.data else None
        
        # TODO: Calculate streak, ranks from database views
        
        return UserStats(
            total_activities=activities.count or 0,
            total_km=current_user.get('total_km', 0),
            total_points=current_user.get('total_points', 0),
            zones_controlled=current_user.get('zones_count', 0),
            team_name=team_name,
            global_rank=None,  # TODO: from leaderboard view
            country_rank=None,
            city_rank=None,
            current_streak_days=0,  # TODO: calculate
            best_streak_days=0  # TODO: calculate
        )
        
    except Exception as e:
        logger.error("Stats fetch error", user_id=current_user['id'], error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user stats"
        )


@router.get("/{user_id}", response_model=UserPublicProfile)
async def get_user_public_profile(user_id: str):
    """
    Get public profile of any user
    
    Returns limited information for privacy
    """
    try:
        result = db.client.table('users')\
            .select('id, username, avatar_url, total_km, total_points, zones_count, team_id')\
            .eq('id', user_id)\
            .eq('is_active', True)\
            .single()\
            .execute()
        
        if not result.data:
            raise UserNotFound(user_id)
        
        return result.data
        
    except UserNotFound:
        raise
    except Exception as e:
        logger.error("User fetch error", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user"
        )


@router.delete("/me", response_model=MessageResponse)
async def delete_current_user_account(
    current_user: dict = Depends(get_current_user)
):
    """
    Delete current user account (soft delete)
    
    Sets is_active = false instead of actually deleting
    """
    try:
        # Soft delete
        db.client.table('users')\
            .update({'is_active': False})\
            .eq('id', current_user['id'])\
            .execute()
        
        logger.info("User account deleted", user_id=current_user['id'])
        
        return MessageResponse(message="Account deleted successfully")
        
    except Exception as e:
        logger.error("Account deletion error", user_id=current_user['id'], error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )
```

---

Continúo con los routers de actividades, teams, zones y leaderboards en el siguiente mensaje para que no sea demasiado largo.

¿Quieres que continúe con el resto de los routers?
