from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime
from enum import Enum

class AuditAction(str, Enum):
    UPLOAD = "upload"
    PROCESS = "process"
    REVIEW = "review"
    EXPORT = "export"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"

class AuditLog(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    action: AuditAction
    resource_type: str  # "invoice", "user", etc.
    resource_id: Optional[str] = None
    description: str
    status: str  # "success", "failed"
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
