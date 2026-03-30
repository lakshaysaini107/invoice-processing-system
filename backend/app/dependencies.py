from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Dict, Any, Optional
from backend.app.config import settings
from backend.database.repositories.user_repo import UserRepository
from backend.database.repositories.invoice_repo import InvoiceRepository
from backend.database.repositories.erp_invoice_repo import ERPInvoiceRepository


# Initialize security scheme
security = HTTPBearer(auto_error=False)


class TokenData:
    """Token claims"""
    def __init__(self, user_id: str, email: str, role: str):
        self.user_id = user_id
        self.email = email
        self.role = role


# Dependency functions for repositories and services
def get_user_repository():
    """Dependency for UserRepository"""
    return UserRepository()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository),
) -> Dict[str, Any]:
    if settings.AUTH_DISABLED:
        return {
            "_id": "public",
            "email": "public@local",
            "full_name": "Public User",
            "company": "Public",
            "role": "admin",
            "is_active": True,
            "created_at": datetime.utcnow(),
        }

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from backend.core.security import verify_token

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_repo.get_by_id(str(user_id))
    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    if settings.AUTH_DISABLED:
        return current_user

    if str(current_user.get("role")) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


def get_invoice_repository():
    """Dependency for InvoiceRepository"""
    return InvoiceRepository()

def get_upload_service():
    """Dependency for UploadService"""
    from backend.services.upload_service import UploadService
    return UploadService()

def get_processing_service():
    """Dependency for ProcessingService"""
    from backend.services.processing_service import ProcessingService
    from backend.ai.preprocessing import PreprocessingEngine
    from backend.ai.ocr_engine import OCREngine
    from backend.ai.layout_detection import LayoutDetectionEngine
    from backend.ai.vision_llm import VisionLLMEngine
    from backend.ai.ner_extraction import NEREngine
    from backend.services.validation_service import ValidationService

    global _processing_service
    if _processing_service is None:
        _processing_service = ProcessingService(
            invoice_repo=get_invoice_repository(),
            preprocessing=PreprocessingEngine(),
            ocr=OCREngine(),
            layout_detection=LayoutDetectionEngine(),
            vision_llm=VisionLLMEngine(),
            ner=NEREngine(),
            validation=ValidationService()
        )

    return _processing_service

def get_review_service():
    """Dependency for ReviewService"""
    from backend.services.review_service import ReviewService
    return ReviewService()

def get_export_service():
    """Dependency for ExportService"""
    from backend.services.export_service import ExportService
    return ExportService()


def get_erp_invoice_repository():
    """Dependency for ERP persistence repository."""
    return ERPInvoiceRepository()


def get_erp_current_invoice_store() -> Dict[str, Any]:
    """Shared in-memory handoff store for ERP demos."""
    global _erp_current_invoice_store
    return _erp_current_invoice_store


# Cache heavy services (OCR/LLM/Spacy) to avoid reloading per-request.
_processing_service = None
_erp_current_invoice_store: Dict[str, Any] = {}
