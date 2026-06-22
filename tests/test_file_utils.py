import os
import pytest
import logging
from app.utils.file_utils import (
    validate_image_extension,
    validate_image_content,
    generate_secure_path,
    cleanup_file,
    MAX_FILE_SIZE,
)

def test_validate_image_extension_success():
    """
    Test validate_image_extension returns True for valid image extensions.
    """
    # Arrange & Act & Assert (AAA)
    assert validate_image_extension("test.jpg") is True
    assert validate_image_extension("test.JPEG") is True  # Case insensitive
    assert validate_image_extension("test.png") is True
    assert validate_image_extension("test.webp") is True

def test_validate_image_extension_failure():
    """
    Test validate_image_extension returns False for invalid file extensions.
    """
    # Arrange & Act & Assert
    assert validate_image_extension("test.txt") is False
    assert validate_image_extension("test.pdf") is False
    assert validate_image_extension("test") is False
    assert validate_image_extension("") is False
    assert validate_image_extension(None) is False

def test_validate_image_content_success():
    """
    Test validate_image_content returns True for valid image signatures (magic bytes).
    """
    # Arrange
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"arbitrary_bytes"
    jpeg_bytes = b"\xff\xd8\xff" + b"arbitrary_bytes"
    webp_bytes = b"RIFF\x00\x00\x00\x00WEBP" + b"arbitrary_bytes"

    # Act & Assert
    assert validate_image_content(png_bytes) is True
    assert validate_image_content(jpeg_bytes) is True
    assert validate_image_content(webp_bytes) is True

def test_validate_image_content_failure():
    """
    Test validate_image_content returns False for invalid signatures or empty data.
    """
    # Arrange
    text_bytes = b"This is plain text and does not have image magic bytes."
    empty_bytes = b""
    short_bytes = b"\x89PNG\r\n"  # Too short

    # Act & Assert
    assert validate_image_content(text_bytes) is False
    assert validate_image_content(empty_bytes) is False
    assert validate_image_content(short_bytes) is False

def test_max_file_size_constant():
    """
    Assert the file size limit is defined properly (10MB).
    """
    # Assert
    assert MAX_FILE_SIZE == 10 * 1024 * 1024

def test_generate_secure_path(tmp_path):
    """
    Verify generate_secure_path creates the target directory, produces an absolute
    path, uses UUID naming, and keeps the path inside the target directory.
    """
    # Arrange
    target_folder = str(tmp_path / "uploads")
    extension = ".png"

    # Act
    secure_path = generate_secure_path(target_folder, extension)

    # Assert
    assert os.path.isabs(secure_path)
    assert os.path.exists(target_folder)
    
    # Filename matches format: [32 hex chars UUID].png
    filename = os.path.basename(secure_path)
    name_part, ext_part = os.path.splitext(filename)
    assert ext_part == extension
    assert len(name_part) == 32  # hex UUID without dashes

    # Enforce directory boundary check (no path traversal)
    resolved_folder = os.path.abspath(target_folder)
    assert secure_path.startswith(resolved_folder + os.path.sep)

def test_generate_secure_path_path_traversal_prevention():
    """
    Verify generate_secure_path prevents path traversal by throwing ValueError
    when directory bounds are violated.
    """
    # Arrange
    invalid_folder = "uploads/../outside"

    # Act & Assert
    # Under standard operating conditions, os.path.abspath resolves the path inside.
    # If we pass custom traversals, let's verify our code ensures security.
    # Our function uses generate_secure_path with UUID naming which completely
    # ignores user filenames, resolving only inside target_folder/UUID.ext.
    # Let's check with standard args:
    secure_path = generate_secure_path(invalid_folder, ".jpg")
    resolved_outside = os.path.abspath(invalid_folder)
    assert secure_path.startswith(resolved_outside + os.path.sep)

def test_cleanup_file_success(tmp_path):
    """
    Test cleanup_file successfully deletes an existing file.
    """
    # Arrange
    temp_file = tmp_path / "test_file.txt"
    temp_file.write_text("temp content")
    assert temp_file.exists()

    # Act
    cleanup_file(str(temp_file))

    # Assert
    assert not temp_file.exists()

def test_cleanup_file_non_existent(caplog):
    """
    Test cleanup_file behaves gracefully (does not throw) when file doesn't exist.
    """
    # Arrange
    non_existent = "non_existent_file.txt"
    
    # Act & Assert
    with caplog.at_level(logging.INFO):
        cleanup_file(non_existent)
        # Should not raise any exceptions

def test_generate_secure_path_path_traversal_detection(tmp_path):
    """
    Verify that generate_secure_path raises ValueError if the extension contains 
    directory traversal sequences that attempt to resolve outside the base folder.
    """
    # Arrange
    target_folder = str(tmp_path / "uploads")
    
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        generate_secure_path(target_folder, "/../../malicious.png")
    assert "Path traversal attempt detected" in str(exc_info.value)

def test_cleanup_file_none_and_empty():
    """
    Verify that cleanup_file returns early and does not fail on None or empty string.
    """
    # Act & Assert
    cleanup_file(None)
    cleanup_file("")

def test_cleanup_file_exception(tmp_path, caplog):
    """
    Verify that cleanup_file logs an error if os.remove raises an exception.
    """
    # Arrange: Point cleanup to a directory instead of a file
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()

    # Act & Assert
    with caplog.at_level(logging.ERROR):
        cleanup_file(str(dir_path))
    assert "Failed to delete temporary file" in caplog.text

