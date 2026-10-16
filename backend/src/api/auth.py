"""
Authentication API endpoints
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.database import get_db
from src.models.user import User
from src.schemas.auth import UserCreate, UserLogin, Token, UserResponse
from src.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    get_current_admin_user
)
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Registrar nuevo usuario
    
    Args:
        user_data: Datos de usuario
        db: Sesión de base de datos
    
    Returns:
        Usuario creado
    """
    try:
        # Check if username exists
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email exists
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_admin=user_data.is_admin
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info("user_registered", username=user_data.username, email=user_data.email)
        
        return UserResponse.model_validate(new_user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("registration_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login con username y password
    
    Args:
        credentials: Username y password
        db: Sesión de base de datos
    
    Returns:
        JWT access token
    """
    try:
        # Find user
        result = await db.execute(
            select(User).where(User.username == credentials.username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning("login_failed_user_not_found", username=credentials.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(credentials.password, user.hashed_password):
            logger.warning("login_failed_invalid_password", username=credentials.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if active
        if not user.is_active:
            logger.warning("login_failed_inactive_user", username=credentials.username)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()
        
        # Create token
        access_token = create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "role": "admin" if user.is_admin else "user"
            }
        )
        
        logger.info("user_logged_in", username=user.username, user_id=user.id)
        
        return Token(access_token=access_token, token_type="bearer")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("login_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener información del usuario autenticado
    
    Args:
        current_user: Usuario del token JWT
        db: Sesión de base de datos
    
    Returns:
        Información del usuario
    """
    try:
        result = await db.execute(
            select(User).where(User.username == current_user["sub"])
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.model_validate(user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_user_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/admin-only")
async def admin_only_route(current_user: dict = Depends(get_current_admin_user)):
    """
    Ruta de ejemplo solo para admins
    
    Args:
        current_user: Usuario admin del token JWT
    
    Returns:
        Mensaje de éxito
    """
    return {
        "message": "Admin access granted",
        "user": current_user["sub"],
        "role": current_user["role"]
    }
