
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    REVIEWER = "reviewer"

class User(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    email: str
    password_hash: str
    full_name: str
    company: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # Preferences
    notifications_enabled: bool = True
    theme: str = "light"  # "light" or "dark"
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    company: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    company: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    theme: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    company: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
