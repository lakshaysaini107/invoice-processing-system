from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.core.security import verify_token
from typing import Dict, Any, Optional
from backend.database.repositories.user_repo import UserRepository
from backend.database.repositories.local_repo import LocalUserRepository, LocalInvoiceRepository
from backend.database.mongodb import MongoDBClient


# Initialize security scheme
security = HTTPBearer(auto_error=False)


class TokenData:
    """Token claims"""
    def __init__(self, user_id: str, email: str, role: str):
        self.user_id = user_id
        self.email = email
        self.role = role


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Validate and extract user from JWT token, return full user dict"""
    if credentials is None:
        return {
            "_id": "public",
            "email": "public@local",
            "role": "user",
            "is_active": True
        }

    token = credentials.credentials

    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get full user from database
    user_repo = get_user_repository()
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Ensure user is admin"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# Dependency functions for repositories and services
def get_user_repository():
    """Dependency for UserRepository"""
    if MongoDBClient.database is None:
        return LocalUserRepository()
    return UserRepository()

def get_invoice_repository():
    """Dependency for InvoiceRepository"""
    from backend.database.repositories.invoice_repo import InvoiceRepository
    if MongoDBClient.database is None:
        return LocalInvoiceRepository()
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


# Cache heavy services (OCR/LLM/Spacy) to avoid reloading per-request.
_processing_service = None
