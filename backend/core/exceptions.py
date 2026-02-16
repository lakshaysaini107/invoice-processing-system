from fastapi import HTTPException, status
from typing import Optional, Dict, Any


class InvoiceProcessingException(Exception):
    """Base exception for invoice processing"""
    def __init__(
        self,
        message: str,
        error_code: str = "PROCESSING_ERROR",
        status_code: int = 400
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class InvalidFileException(InvoiceProcessingException):
    """Raised when file format/size is invalid"""
    def __init__(self, message: str):
        super().__init__(
            message,
            error_code="INVALID_FILE",
            status_code=400
        )


class ProcessingTimeoutException(InvoiceProcessingException):
    """Raised when processing exceeds timeout"""
    def __init__(self, message: str = "Processing timeout"):
        super().__init__(
            message,
            error_code="PROCESSING_TIMEOUT",
            status_code=408
        )


class DatabaseException(InvoiceProcessingException):
    """Raised for database errors"""
    def __init__(self, message: str = "Database error"):
        super().__init__(
            message,
            error_code="DATABASE_ERROR",
            status_code=500
        )


class AuthenticationException(InvoiceProcessingException):
    """Raised for authentication failures"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message,
            error_code="AUTH_ERROR",
            status_code=401
        )


class UnauthorizedException(InvoiceProcessingException):
    """Raised for insufficient permissions"""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(
            message,
            error_code="UNAUTHORIZED",
            status_code=403
        )


# Exception handlers for FastAPI
async def invoice_exception_handler(request, exc: InvoiceProcessingException):
    """Handle custom exceptions"""
    return {
        "error": True,
        "error_code": exc.error_code,
        "message": exc.message,
        "status_code": exc.status_code