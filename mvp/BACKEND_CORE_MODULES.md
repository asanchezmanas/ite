# 🔧 Backend Core Modules Implementation

## 📁 app/core/config.py

```python
"""
Application configuration and settings
Using pydantic-settings for type-safe environment variables
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    APP_NAME: str = "Territory Conquest API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="info", env="LOG_LEVEL")
    
    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=1, env="WORKERS")
    
    # Database - Supabase
    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")
    SUPABASE_KEY: str = Field(..., env="SUPABASE_KEY")
    SUPABASE_SERVICE_KEY: Optional[str] = Field(None, env="SUPABASE_SERVICE_KEY")
    
    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY", min_length=32)
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        env="CORS_ORIGINS"
    )
    CORS_CREDENTIALS: bool = Field(default=True, env="CORS_CREDENTIALS")
    CORS_METHODS: List[str] = Field(default=["*"], env="CORS_METHODS")
    CORS_HEADERS: List[str] = Field(default=["*"], env="CORS_HEADERS")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=False, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Redis (optional - for caching/rate limiting)
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")
    REDIS_ENABLED: bool = Field(default=False, env="REDIS_ENABLED")
    
    # External Services
    SENTRY_DSN: Optional[str] = Field(None, env="SENTRY_DSN")
    SENTRY_ENVIRONMENT: Optional[str] = Field(None, env="SENTRY_ENVIRONMENT")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1, env="SENTRY_TRACES_SAMPLE_RATE")
    
    # Monitoring
    ENABLE_METRICS: bool = Field(default=False, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    # Business Logic
    POINTS_PER_KM: int = Field(default=10, env="POINTS_PER_KM")
    ZONE_CONTROL_THRESHOLD_KM: float = Field(default=5.0, env="ZONE_CONTROL_THRESHOLD_KM")
    DEFAULT_CITY: str = Field(default="Barcelona", env="DEFAULT_CITY")
    H3_RESOLUTION: int = Field(default=9, env="H3_RESOLUTION")
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(default=20, env="DEFAULT_PAGE_SIZE")
    MAX_PAGE_SIZE: int = Field(default=100, env="MAX_PAGE_SIZE")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        allowed = ["debug", "info", "warning", "error", "critical"]
        if v.lower() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.lower()
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
```

---

## 🔐 app/core/security.py

```python
"""
Security utilities: JWT, password hashing, token management
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from .config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """Centralized security management"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(
        subject: str,
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create JWT access token
        
        Args:
            subject: Usually user ID
            expires_delta: Token expiration time
            additional_claims: Extra data to include in token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        if additional_claims:
            to_encode.update(additional_claims)
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(subject: str) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Decode and validate JWT token
        
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def validate_token_type(payload: Dict[str, Any], expected_type: str):
        """Validate token type (access or refresh)"""
        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}"
            )
    
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """
        Validate password meets strength requirements
        
        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        """
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        return has_upper and has_lower and has_digit


# Global security manager instance
security = SecurityManager()
```

---

## ⚠️ app/core/exceptions.py

```python
"""
Custom exceptions for the application
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class TerritoryException(HTTPException):
    """Base exception for Territory Conquest"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code or self.__class__.__name__


# Authentication Exceptions
class AuthenticationError(TerritoryException):
    """Base authentication error"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class InvalidCredentials(AuthenticationError):
    def __init__(self):
        super().__init__("Invalid email or password")


class TokenExpired(AuthenticationError):
    def __init__(self):
        super().__init__("Token has expired")


class InvalidToken(AuthenticationError):
    def __init__(self):
        super().__init__("Invalid token")


# Authorization Exceptions
class AuthorizationError(TerritoryException):
    """Base authorization error"""
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class InsufficientPermissions(AuthorizationError):
    def __init__(self):
        super().__init__("You don't have permission to perform this action")


class NotResourceOwner(AuthorizationError):
    def __init__(self):
        super().__init__("You can only modify your own resources")


# Validation Exceptions
class ValidationError(TerritoryException):
    """Base validation error"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class InvalidInput(ValidationError):
    pass


class WeakPassword(ValidationError):
    def __init__(self):
        super().__init__(
            "Password must be at least 8 characters and contain uppercase, "
            "lowercase, and numbers"
        )


# Resource Exceptions
class ResourceNotFound(TerritoryException):
    """Resource not found"""
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with id '{identifier}' not found"
        )


class UserNotFound(ResourceNotFound):
    def __init__(self, user_id: str):
        super().__init__("User", user_id)


class TeamNotFound(ResourceNotFound):
    def __init__(self, team_id: str):
        super().__init__("Team", team_id)


class ActivityNotFound(ResourceNotFound):
    def __init__(self, activity_id: str):
        super().__init__("Activity", activity_id)


class ZoneNotFound(ResourceNotFound):
    def __init__(self, zone_id: str):
        super().__init__("Zone", zone_id)


# Conflict Exceptions
class ResourceConflict(TerritoryException):
    """Resource conflict"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class UserAlreadyExists(ResourceConflict):
    def __init__(self, field: str, value: str):
        super().__init__(f"User with {field} '{value}' already exists")


class AlreadyInTeam(ResourceConflict):
    def __init__(self):
        super().__init__("You are already in a team")


class TeamNameTaken(ResourceConflict):
    def __init__(self, name: str):
        super().__init__(f"Team name '{name}' is already taken")


# Business Logic Exceptions
class BusinessLogicError(TerritoryException):
    """Base business logic error"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class InvalidActivityData(BusinessLogicError):
    def __init__(self, reason: str):
        super().__init__(f"Invalid activity data: {reason}")


class InsufficientDistance(InvalidActivityData):
    def __init__(self):
        super().__init__("Distance must be at least 0.1 km")


class InvalidCoordinates(InvalidActivityData):
    def __init__(self):
        super().__init__("Invalid latitude or longitude")


# Rate Limiting Exception
class RateLimitExceeded(TerritoryException):
    """Rate limit exceeded"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds",
            headers={"Retry-After": str(retry_after)}
        )


# Database Exceptions
class DatabaseError(TerritoryException):
    """Database operation failed"""
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class DatabaseConnectionError(DatabaseError):
    def __init__(self):
        super().__init__("Could not connect to database")


# External Service Exceptions
class ExternalServiceError(TerritoryException):
    """External service error"""
    def __init__(self, service: str, detail: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service} service error: {detail}"
        )


class GeocodingError(ExternalServiceError):
    def __init__(self, detail: str):
        super().__init__("Geocoding", detail)
```

---

## 📊 app/core/logging.py

```python
"""
Structured logging configuration
"""

import logging
import sys
from typing import Any
from datetime import datetime
import structlog
from .config import settings


def setup_logging():
    """Configure structured logging"""
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper())
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.is_production
            else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


# Create logger instances for different modules
auth_logger = get_logger("auth")
api_logger = get_logger("api")
db_logger = get_logger("database")
service_logger = get_logger("service")
```

---

## 🗄️ app/core/database.py

```python
"""
Database connection and utilities
"""

from typing import Optional
from supabase import create_client, Client
from functools import lru_cache
from .config import settings
from .logging import db_logger
from .exceptions import DatabaseConnectionError


class DatabaseManager:
    """Manage Supabase connections"""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._service_client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Get regular Supabase client"""
        if self._client is None:
            try:
                self._client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY
                )
                db_logger.info("Supabase client initialized")
            except Exception as e:
                db_logger.error("Failed to initialize Supabase client", error=str(e))
                raise DatabaseConnectionError()
        
        return self._client
    
    @property
    def service_client(self) -> Client:
        """Get service role Supabase client (admin privileges)"""
        if self._service_client is None:
            if not settings.SUPABASE_SERVICE_KEY:
                raise ValueError("SUPABASE_SERVICE_KEY not configured")
            
            try:
                self._service_client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_KEY
                )
                db_logger.info("Supabase service client initialized")
            except Exception as e:
                db_logger.error("Failed to initialize service client", error=str(e))
                raise DatabaseConnectionError()
        
        return self._service_client
    
    def health_check(self) -> bool:
        """Check database connection health"""
        try:
            # Simple query to check connection
            result = self.client.table('users').select('id').limit(1).execute()
            return True
        except Exception as e:
            db_logger.error("Database health check failed", error=str(e))
            return False


@lru_cache()
def get_database() -> DatabaseManager:
    """Get cached database manager instance"""
    return DatabaseManager()


# Global database instance
db = get_database()
```

---

## 🎯 Usage Examples

### Config
```python
from app.core.config import settings

# Access settings
print(settings.APP_NAME)
print(settings.ENVIRONMENT)
print(settings.SUPABASE_URL)

# Check environment
if settings.is_production:
    # Production logic
    pass
```

### Security
```python
from app.core.security import security

# Hash password
hashed = security.hash_password("MyPassword123")

# Verify password
is_valid = security.verify_password("MyPassword123", hashed)

# Create tokens
access_token = security.create_access_token(subject="user_id_123")
refresh_token = security.create_refresh_token(subject="user_id_123")

# Decode token
payload = security.decode_token(access_token)
user_id = payload["sub"]

# Validate password strength
is_strong = security.validate_password_strength("WeakPass")  # False
```

### Exceptions
```python
from app.core.exceptions import UserNotFound, InvalidCredentials

# Raise custom exceptions
raise UserNotFound(user_id="123")
raise InvalidCredentials()

# Use in route handlers
@router.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await find_user(user_id)
    if not user:
        raise UserNotFound(user_id)
    return user
```

### Logging
```python
from app.core.logging import get_logger

logger = get_logger(__name__)

logger.info("User logged in", user_id="123", ip="1.2.3.4")
logger.error("Failed to process activity", activity_id="456", error="GPS invalid")
logger.debug("Processing zone", zone_id="789", h3_index="891f1d...")
```

### Database
```python
from app.core.database import db

# Get client
supabase = db.client

# Query
result = supabase.table('users').select('*').eq('id', user_id).execute()

# Insert
supabase.table('activities').insert(activity_data).execute()

# Health check
is_healthy = db.health_check()
```

---

Continúo con los demás módulos (API, Services, Schemas) en el siguiente archivo.
