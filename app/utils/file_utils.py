import os
import uuid
import logging
from typing import Set
from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Derive settings dynamically from settings object
ALLOWED_EXTENSIONS: Set[str] = settings.allowed_extensions
MAX_FILE_SIZE: int = settings.max_upload_size_mb * 1024 * 1024

def validate_image_extension(filename: str) -> bool:
    """
    Validate that the file extension is one of the allowed image formats.
    """
    if not filename:
        return False
    _, ext = os.path.splitext(filename.lower())
    return ext in settings.allowed_extensions

def validate_image_content(file_bytes: bytes) -> bool:
    """
    Validate file content using magic bytes to ensure it is a valid image.
    The validation is conditioned on settings.allowed_magic_signatures.
    """
    # Minimum size to check headers
    if len(file_bytes) < 12:
        return False

    # Check magic bytes for PNG, JPEG, WEBP based on allowed signatures
    is_png = "png" in settings.allowed_magic_signatures and file_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    is_jpeg = "jpeg" in settings.allowed_magic_signatures and file_bytes.startswith(b"\xff\xd8\xff")
    is_webp = "webp" in settings.allowed_magic_signatures and file_bytes.startswith(b"RIFF") and file_bytes[8:12] == b"WEBP"

    return is_png or is_jpeg or is_webp

def generate_secure_path(folder: str, extension: str) -> str:
    """
    Generate an absolute, secure, unpredictable file path within the specified folder.
    Ensures that path traversal is prevented by ignoring user filenames.
    """
    # Create the directory if it does not exist
    os.makedirs(folder, exist_ok=True)
    
    # Generate unique UUID filename
    random_filename = f"{uuid.uuid4().hex}{extension}"
    
    # Securely resolve path
    base_dir = os.path.abspath(folder)
    target_path = os.path.abspath(os.path.join(base_dir, random_filename))
    
    # Enforce directory boundary check (to prevent path traversal)
    if not target_path.startswith(base_dir + os.path.sep) and target_path != base_dir:
        raise ValueError("Path traversal attempt detected or invalid directory structure.")
        
    return target_path

def cleanup_file(file_path: str) -> None:
    """
    Safely delete a file from the filesystem.
    """
    if not file_path:
        return
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info("Successfully removed temporary file: %s", file_path)
    except Exception as e:
        logger.error("Failed to delete temporary file %s: %s", file_path, str(e))
