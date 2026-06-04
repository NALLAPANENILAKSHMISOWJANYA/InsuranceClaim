"""
Insurance Claim Pre-Assurance – File Utilities
Safe file storage with MIME validation and size enforcement.
"""
import uuid
import logging
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings
from app.utils.exceptions import UnsupportedFileTypeError, FileTooLargeError

logger = logging.getLogger(__name__)

# Max bytes derived from config (convert MB → bytes)
_MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


def validate_upload(file: UploadFile) -> None:
    """
    Raise an HTTP exception if the file's content type is not allowed.
    NOTE: File size is checked during streaming in save_upload_file().
    """
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise UnsupportedFileTypeError(file.content_type)


async def save_upload_file(file: UploadFile, claim_id: str, document_type: str) -> tuple[Path, int]:
    """
    Stream an uploaded file to disk inside uploads/{claim_id}/.
    Returns (saved_path, size_in_bytes).
    Raises FileTooLargeError if the file exceeds MAX_FILE_SIZE_MB.
    """
    destination_dir = settings.UPLOAD_DIR / claim_id
    destination_dir.mkdir(parents=True, exist_ok=True)

    extension = _get_extension(file.content_type)
    unique_name = f"{document_type}_{uuid.uuid4().hex}{extension}"
    destination = destination_dir / unique_name

    total_bytes = 0
    chunk_size = 64 * 1024  # 64 KB chunks

    with destination.open("wb") as out_file:
        while chunk := await file.read(chunk_size):
            total_bytes += len(chunk)
            if total_bytes > _MAX_BYTES:
                destination.unlink(missing_ok=True)
                raise FileTooLargeError(settings.MAX_FILE_SIZE_MB)
            out_file.write(chunk)

    logger.info(
        "File saved",
        extra={"claim_id": claim_id, "file": unique_name, "bytes": total_bytes},
    )
    return destination, total_bytes


def _get_extension(mime_type: str) -> str:
    """Map MIME type to file extension."""
    mapping = {
        "application/pdf": ".pdf",
        "image/jpeg": ".jpg",
        "image/png": ".png",
    }
    return mapping.get(mime_type, ".bin")
