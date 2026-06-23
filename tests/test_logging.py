import os
import logging
import importlib
import pytest
from app.config import settings
from app.utils.logging_config import setup_logging
from app.config.base import Settings

def test_logging_files_created(client):
    """
    Verify that app.log, error.log, and access.log are successfully created
    in the configured logs directory at startup.
    """
    # Arrange & Act: client fixture triggers lifespan and logging initialization
    log_dir = settings.log_dir
    app_log = os.path.join(log_dir, settings.app_log_filename)
    error_log = os.path.join(log_dir, settings.error_log_filename)
    access_log = os.path.join(log_dir, settings.access_log_filename)

    # Assert: Verify log file creation
    assert os.path.exists(app_log)
    assert os.path.exists(error_log)
    assert os.path.exists(access_log)



def test_log_rotation(tmp_path):
    """
    Verify that RotatingFileHandler rotates log files when they exceed log_rotation_max_bytes size.
    """
    # Arrange: Setup settings with a very small log limit (50 bytes)
    rot_settings = Settings()
    rot_settings.log_dir = str(tmp_path / "rotation_logs")
    rot_settings.enable_file_logging = True
    rot_settings.log_rotation_max_bytes = 50
    rot_settings.log_backup_count = 2
    rot_settings.app_log_filename = "app_rot.log"
    rot_settings.error_log_filename = "error_rot.log"
    rot_settings.access_log_filename = "access_rot.log"

    # Setup the logger with rotation settings
    setup_logging(rot_settings)
    logger = logging.getLogger()

    # Act: Write logs that exceed 50 bytes (twice) to trigger rotation
    logger.info("X" * 60)
    logger.info("Y" * 60)

    # Assert: The rotated file should exist (app_rot.log.1)
    rotated_file_path = os.path.join(rot_settings.log_dir, "app_rot.log.1")
    assert os.path.exists(rotated_file_path)
    
    # Cleanup handlers to release lock on files
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

def test_middleware_exception_logging(tmp_path):
    """
    Verify that if an unhandled exception propagates through the request logging middleware,
    it logs a 500 error entry to access_logger and returns a 500 response.
    """
    from app.config import settings as live_settings

    # Save original log_dir so we can restore it after this test
    original_log_dir = live_settings.log_dir

    # Point logging at a fresh tmp dir so file handlers are current and isolated
    exc_log_dir = str(tmp_path / "exc_logs")
    live_settings.log_dir = exc_log_dir
    setup_logging(live_settings)

    # Arrange: Setup a bad state that throws an unhandled RuntimeError when accessing 'model'
    class BadState:
        @property
        def model(self):
            raise RuntimeError("Database connection failure")

        @model.setter
        def model(self, value):
            pass  # Allow lifespan shutdown (app.state.model = None) to complete

    from fastapi.testclient import TestClient
    from app.main import app

    try:
        # Save original state
        original_state = app.state
        
        # Create a local client instance that handles server exceptions instead of re-raising them
        with TestClient(app, raise_server_exceptions=False) as exc_client:
            # Override state on this app instance
            exc_client.app.state = BadState()

            access_log_path = os.path.join(exc_log_dir, live_settings.access_log_filename)

            if os.path.exists(access_log_path):
                open(access_log_path, "w").close()

            # Act: Request the health endpoint
            response = exc_client.get("/health")

            # Assert: Verify response code and access log error details
            assert response.status_code == 500
            with open(access_log_path, "r") as f:
                log_content = f.read()
            assert "500" in log_content
            assert "Database connection failure" in log_content
    finally:
        # Restore app state
        app.state = original_state
        # Restore original log_dir so subsequent tests are not affected
        live_settings.log_dir = original_log_dir
        setup_logging(live_settings)






