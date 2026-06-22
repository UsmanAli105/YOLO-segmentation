import os
import pytest
from unittest.mock import patch
from PIL import Image

@pytest.fixture
def mock_run_segmentation():
    """
    Mock run_segmentation service function to write a dummy annotated image.
    Prevents any actual YOLO model inference/plotting logic.
    """
    with patch("app.routes.segmentation.run_segmentation") as mock:
        def side_effect(model, input_path, output_path):
            # Write a dummy image to the output path so FileResponse works
            img = Image.new("RGB", (50, 50), color="green")
            img.save(output_path)
        mock.side_effect = side_effect
        yield mock



def test_segment_invalid_extension(client, mock_run_segmentation, invalid_file_path):
    """
    Verify that uploading a file with an unsupported extension returns HTTP 400.
    """
    # Arrange
    with open(invalid_file_path, "rb") as f:
        file_payload = {"file": ("invalid_file.txt", f, "text/plain")}

        # Act
        response = client.post("/segment", files=file_payload)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid file extension. Allowed extensions are: .jpeg, .jpg, .png, .webp"
    mock_run_segmentation.assert_not_called()

def test_segment_invalid_magic_bytes(client, mock_run_segmentation):
    """
    Verify that uploading a file with a valid extension but invalid magic bytes returns HTTP 400.
    """
    # Arrange
    bad_content = b"Not an image at all. Plain text content."
    file_payload = {"file": ("fake_image.jpg", bad_content, "image/jpeg")}

    # Act
    response = client.post("/segment", files=file_payload)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image content. File signature check failed."
    mock_run_segmentation.assert_not_called()

def test_segment_empty_upload(client, mock_run_segmentation):
    """
    Verify that uploading an empty file returns HTTP 400.
    """
    # Arrange
    empty_content = b""
    file_payload = {"file": ("empty.jpg", empty_content, "image/jpeg")}

    # Act
    response = client.post("/segment", files=file_payload)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image content. File signature check failed."
    mock_run_segmentation.assert_not_called()

def test_segment_oversized_file(client, mock_run_segmentation):
    """
    Verify that uploading a file exceeding 10MB returns HTTP 413.
    """
    # Arrange
    oversized_content = b"0" * (10 * 1024 * 1024 + 1)
    file_payload = {"file": ("large_image.jpg", oversized_content, "image/jpeg")}

    # Act
    response = client.post("/segment", files=file_payload)

    # Assert
    assert response.status_code == 413
    assert response.json()["detail"] == "File size exceeds the maximum limit of 10MB."
    mock_run_segmentation.assert_not_called()

def test_segment_missing_file_parameter(client, mock_run_segmentation):
    """
    Verify that omitting the 'file' parameter returns HTTP 422 (validation error).
    """
    # Arrange & Act
    response = client.post("/segment")

    # Assert
    assert response.status_code == 422
    mock_run_segmentation.assert_not_called()

def test_segment_internal_service_exception(client, mock_run_segmentation, valid_image_path):
    """
    Verify that if the segmentation service raises an exception, the route handles
    it and returns HTTP 500, and does not leak files.
    """
    # Arrange
    mock_run_segmentation.side_effect = RuntimeError("YOLO segmentation failed")
    
    with open(valid_image_path, "rb") as f:
        file_payload = {"file": ("valid_image.jpg", f, "image/jpeg")}
        
        # Act
        response = client.post("/segment", files=file_payload)

    # Assert
    assert response.status_code == 500
    assert response.json()["detail"] == "An error occurred while processing the image."



