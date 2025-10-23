# app/api/auth.py

from fastapi import APIRouter, HTTPException, status
from app.models.user import UserCreate, UserLogin, User, Token
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.database import supabase

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate):
    """Registrar nuevo usuario"""
    
    # Verificar email único
    email_check = supabase.table('users').select('id').eq('email', user_in.email).execute()
    if email_check.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Verificar username único
    username_check = supabase.table('users').select('id').eq('username', user_in.username).execute()
    if username_check.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Crear usuario
    user_data = {
        'email': user_in.email,
        'username': user_in.username,
        'full_name': user_in.full_name,
        'password_hash': get_password_hash(user_in.password)
    }
    
    response = supabase.table('users').insert(user_data).execute()
    user = response.data[0]
    
    # Crear token
    access_token = create_access_token(data={"sub": user['id']})
    
    return Token(access_token=access_token)


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login de usuario"""
    
    # Buscar usuario por email
    response = supabase.table('users').select('*').eq('email', credentials.email).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    user = response.data[0]
    
    # Verificar password
    if not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verificar usuario activo
    if not user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Crear token
    access_token = create_access_token(data={"sub": user['id']})
    
    return Token(access_token=access_token)


@router.post("/logout")
async def logout():
    """Logout (cliente debe eliminar token)"""
    return {"message": "Successfully logged out"}
