import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils.logging_config import setup_logging


@pytest.fixture(scope="session", autouse=True)
def mock_yolo_class():
    """
    Session-level fixture to mock the YOLO class in app.main.
    Prevents the actual YOLO model from loading or downloading from the internet during lifespan initialization.
    """
    with patch("app.main.YOLO") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def client(mock_yolo_class, tmp_path):
    """
    Provide a FastAPI TestClient with the mocked lifespan app.
    Dynamically overrides settings directory parameters (uploads, outputs, models, logs)
    to point to pytest's temporary directory before importing app.main.
    This guarantees full filesystem isolation during test execution.
    Settings are fully restored after each test to prevent state leaking between tests.
    """
    from app.config import settings

    # --- Save original settings values so they can be restored after this test ---
    original_uploads = settings.uploads_directory
    original_outputs = settings.outputs_directory
    original_models = settings.models_directory
    original_log_dir = settings.log_dir

    # Define temporary directories
    test_upload_dir = tmp_path / "uploads"
    test_output_dir = tmp_path / "outputs"
    test_models_dir = tmp_path / "models"
    test_log_dir = tmp_path / "logs"

    test_upload_dir.mkdir(parents=True, exist_ok=True)
    test_output_dir.mkdir(parents=True, exist_ok=True)
    test_models_dir.mkdir(parents=True, exist_ok=True)
    test_log_dir.mkdir(parents=True, exist_ok=True)

    # Patch global settings to use isolated tmp directories for this test
    settings.uploads_directory = str(test_upload_dir)
    settings.outputs_directory = str(test_output_dir)
    settings.models_directory = str(test_models_dir)
    settings.log_dir = str(test_log_dir)

    # Re-initialize logging so file handlers point to the patched tmp_path log dir.
    # setup_logging() is called once at module import time in app.main, so we must
    # call it again here after overriding log_dir to get handlers targeting the right path.
    setup_logging(settings)

    # Import app now so it uses the modified settings object for logging setup
    from app.main import app
    from fastapi.testclient import TestClient

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # --- Restore original settings so subsequent tests are not affected ---
        settings.uploads_directory = original_uploads
        settings.outputs_directory = original_outputs
        settings.models_directory = original_models
        settings.log_dir = original_log_dir
        # Re-initialize logging back to the original log dir
        setup_logging(settings)


@pytest.fixture
def fixtures_dir() -> str:
    """
    Return the absolute path to the tests/fixtures directory.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))


@pytest.fixture
def valid_image_path(fixtures_dir: str) -> str:
    """
    Return the path to the valid JPEG image fixture.
    """
    return os.path.join(fixtures_dir, "valid_image.jpg")


@pytest.fixture
def invalid_file_path(fixtures_dir: str) -> str:
    """
    Return the path to the invalid text file fixture.
    """
    return os.path.join(fixtures_dir, "invalid_file.txt")
