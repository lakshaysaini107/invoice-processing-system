import aiofiles
import os
from pathlib import Path
from fastapi import UploadFile
from typing import Optional
from backend.app.config import settings
from backend.core.logging import logger
import mimetypes

class UploadService:
    """Handle file upload, storage, and validation"""

    ALLOWED_FORMATS = {"application/pdf", "image/jpeg", "image/png", "image/tiff"}
    MAX_FILE_SIZE = 20 * 1024 * 1024 # 20MB

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def validate_file(self, file: UploadFile) -> bool:
        """Validate file type and size"""
        # Check MIME type
        mime_type = file.content_type
        if mime_type not in self.ALLOWED_FORMATS:
            raise ValueError(
                f"Invalid file format. Allowed: PDF, JPEG, PNG, TIFF. Got: {mime_type}"
            )

        # Check file size
        # Note: Ideally, check Content-Length header first to avoid reading large files
        file_size = 0
        chunk_size = 1024 * 1024 # 1MB chunks
        
        # Read first chunk to ensure we can read it, but for size we might need spool
        # For simplicity in this example, we assume file is spooled or in memory
        file.file.seek(0, 2) # Seek to end
        file_size = file.file.tell()
        await file.seek(0) # Reset to start

        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File size exceeds limit. Max: 20MB, Got: {file_size / (1024*1024):.2f}MB"
            )

        return True

    async def save_file(
        self,
        file: UploadFile,
        invoice_id: str,
        user_id: str
    ) -> str:
        """Save uploaded file to disk"""
        # Create user-specific directory
        user_dir = self.upload_dir / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_extension = Path(file.filename).suffix
        if not file_extension:
            # Fallback extension inference
            file_extension = mimetypes.guess_extension(file.content_type) or ".bin"
            
        saved_filename = f"{invoice_id}{file_extension}"
        file_path = user_dir / saved_filename

        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            while content := await file.read(1024 * 1024):  # Read in 1MB chunks
                await f.write(content)

        logger.info(f"File saved: {file_path}")
        return str(file_path)

    async def delete_file(self, file_path: str) -> bool:
        """Delete uploaded file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
        
        return False

    async def get_file_info(self, file_path: str) -> dict:
        """Get file metadata"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_stat = os.stat(file_path)

        return {
            "path": file_path,
            "size": file_stat.st_size,
            "created_at": file_stat.st_ctime,
            "extension": Path(file_path).suffix
        }
