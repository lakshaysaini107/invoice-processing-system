from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.app.dependencies import get_user_repository
from backend.database.repositories.user_repo import UserRepository

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# ==================== Schemas ====================

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str
    full_name: str
    company: Optional[str] = None
    created_at: datetime

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    company: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    company: str
    created_at: datetime

# ==================== Endpoints ====================

@router.post("/register", response_model=dict)
async def register(request: RegisterRequest, user_repo: UserRepository = Depends(get_user_repository)):
    """Register a new user"""
    existing_user = await user_repo.get_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = hash_password(request.password)
    user_data = {
        "email": request.email,
        "password_hash": hashed_password,
        "full_name": request.full_name,
        "company": request.company,
        "role": "user",
        "created_at": datetime.utcnow()
    }
    
    user = await user_repo.create(user_data)
    return {"message": "User registered successfully", "user_id": str(user["_id"])}

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, user_repo: UserRepository = Depends(get_user_repository)):
    """Authenticate user and return JWT token"""
    user = await user_repo.get_by_email(request.email)

    if not user or not verify_password(request.password, user.get("password_hash")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = create_access_token(
        data={"sub": str(user["_id"]), "email": user["email"], "role": user["role"]}
    )
    
    return LoginResponse(
        access_token=access_token,
        user_id=str(user["_id"]),
        email=user["email"],
        role=user["role"],
        full_name=user["full_name"],
        company=user.get("company"),
        created_at=user.get("created_at") or datetime.utcnow(),
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        company=current_user.get("company"),
        created_at=current_user.get("created_at")
    )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user (invalidates token on frontend)"""
    return {"message": "Logged out successfully"}
