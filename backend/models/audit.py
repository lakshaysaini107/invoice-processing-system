from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AuditLog(BaseModel):
    id: Optional[str] = None
    invoice_id: str
    user_id: Optional[str] = "system"
    action: str
    changes: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
