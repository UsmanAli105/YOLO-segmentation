import os
import pytest
import numpy as np
from unittest.mock import MagicMock
from app.services.yolo_service import run_segmentation

def test_run_segmentation_success(valid_image_path, tmp_path):
    """
    Test run_segmentation with a mocked YOLO model.
    It should successfully run inference, extract the plotted BGR numpy array,
    convert it to RGB, and save it to the output path.
    """
    # Arrange: Setup mocked model, results list, and dummy BGR numpy array
    mock_model = MagicMock()
    mock_result = MagicMock()
    dummy_bgr = np.zeros((10, 10, 3), dtype=np.uint8)
    mock_result.plot.return_value = dummy_bgr
    mock_model.return_value = [mock_result]

    output_path = str(tmp_path / "output_annotated.jpg")

    # Act: Invoke the service function
    run_segmentation(mock_model, valid_image_path, output_path)

    # Assert: Verify file creation and mock interactions
    assert os.path.exists(output_path)
    mock_model.assert_called_once_with(
        valid_image_path,
        conf=0.25,
        iou=0.7,
        max_det=300,
        imgsz=640,
        device="cpu"
    )
    mock_result.plot.assert_called_once()

def test_run_segmentation_file_not_found(tmp_path):
    """
    Verify that run_segmentation raises FileNotFoundError if the input path does not exist.
    """
    # Arrange: Setup mock and non-existent path
    mock_model = MagicMock()
    non_existent_path = "non_existent_image.jpg"
    output_path = str(tmp_path / "output_annotated.jpg")

    # Act & Assert: Invoke and verify exception
    with pytest.raises(FileNotFoundError) as exc_info:
        run_segmentation(mock_model, non_existent_path, output_path)
    assert "Input image not found" in str(exc_info.value)

def test_run_segmentation_no_results(valid_image_path, tmp_path):
    """
    Verify that run_segmentation raises RuntimeError if the model returns empty results list.
    """
    # Arrange: Model returns empty results list
    mock_model = MagicMock()
    mock_model.return_value = []
    output_path = str(tmp_path / "output_annotated.jpg")

    # Act & Assert: Invoke and verify exception
    with pytest.raises(RuntimeError) as exc_info:
        run_segmentation(mock_model, valid_image_path, output_path)
    assert "YOLO segmentation failed" in str(exc_info.value)
