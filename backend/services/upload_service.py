import os
import aiofiles
from fastapi import UploadFile
from backend.app.config import settings
from backend.core.exceptions import ValidationException
from backend.database.repositories.invoice_repo import invoice_repo
from backend.models.inoice import InvoiceCreate, InvoiceOut


class UploadService:
    def validate_file(self, file: UploadFile):
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        allowed_formats = settings.get_allowed_formats()
        if ext not in allowed_formats:
            raise ValidationException(f"File extension '.{ext}' is not supported. Allowed: {allowed_formats}")

    async def save_uploaded_file(self, file: UploadFile, user_id: str = "default_user") -> InvoiceOut:
        self.validate_file(file)

        user_upload_dir = os.path.join(settings.UPLOAD_DIR, user_id)
        os.makedirs(user_upload_dir, exist_ok=True)

        file_path = os.path.join(user_upload_dir, file.filename)
        content = await file.read()
        file_size = len(content)

        if file_size > settings.MAX_FILE_SIZE:
            raise ValidationException(f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE} bytes.")

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        invoice_in = InvoiceCreate(
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            user_id=user_id,
        )
        return await invoice_repo.create(invoice_in)


upload_service = UploadService()
