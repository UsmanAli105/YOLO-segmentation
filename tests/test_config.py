import os
import sys
import importlib
import pytest
from pydantic import ValidationError

def test_config_loading_local(monkeypatch):
    """
    Verify that APP_ENV=local loads the local settings overrides.
    """
    # Arrange
    monkeypatch.setenv("APP_ENV", "local")
    
    # Act
    import app.config
    importlib.reload(app.config)
    
    # Assert
    assert app.config.env == "local"
    assert app.config.settings.debug_mode is True
    assert app.config.settings.log_level == "DEBUG"
    assert app.config.settings.reload is True

def test_config_loading_prod(monkeypatch):
    """
    Verify that APP_ENV=prod loads prod settings overrides.
    """
    # Arrange
    monkeypatch.setenv("APP_ENV", "prod")
    
    # Act
    import app.config
    importlib.reload(app.config)
    
    # Assert
    assert app.config.env == "prod"
    assert app.config.settings.debug_mode is False
    assert app.config.settings.log_level == "ERROR"
    assert app.config.settings.swagger_enabled is False
    assert app.config.settings.redoc_enabled is False
    assert app.config.settings.enable_openapi is False

def test_config_default_fallback(monkeypatch):
    """
    Verify that if APP_ENV is unset, the system defaults to 'local'.
    """
    # Arrange
    monkeypatch.delenv("APP_ENV", raising=False)
    
    # Act
    import app.config
    importlib.reload(app.config)
    
    # Assert
    assert app.config.env == "local"

def test_config_empty_string_fallback(monkeypatch):
    """
    Verify that if APP_ENV is set to an empty string, the system defaults to 'local'.
    """
    # Arrange
    monkeypatch.setenv("APP_ENV", "")
    
    # Act
    import app.config
    importlib.reload(app.config)
    
    # Assert
    assert app.config.env == "local"

def test_config_env_variable_overrides(monkeypatch):
    """
    Verify that environment variables take precedence over file configs.
    """
    # Arrange
    monkeypatch.setenv("APP_ENV", "local")
    # Set overrides for app name and confidence threshold
    monkeypatch.setenv("APP_NAME", "Env Override App Name")
    monkeypatch.setenv("CONFIDENCE_THRESHOLD", "0.85")
    
    # Act
    import app.config
    importlib.reload(app.config)
    
    # Assert
    assert app.config.settings.app_name == "Env Override App Name"
    assert app.config.settings.confidence_threshold == 0.85

def test_config_invalid_types_raise_validation_error(monkeypatch):
    """
    Verify that loading a config with invalid data types raises a ValidationError.
    """
    # Arrange: set port to an invalid non-integer string
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("PORT", "invalid-port-string")
    
    # Act & Assert
    import app.config
    with pytest.raises(ValidationError):
        importlib.reload(app.config)

def test_config_loading_dev(monkeypatch):
    """
    Verify that APP_ENV=dev loads the dev configuration.
    """
    # Arrange
    monkeypatch.setenv("APP_ENV", "dev")
    
    # Act
    import app.config
    importlib.reload(app.config)
    
    # Assert
    assert app.config.env == "dev"
    assert app.config.settings.debug_mode is True
    assert app.config.settings.log_level == "INFO"

def test_config_loading_sit(monkeypatch):
    """
    Verify that APP_ENV=sit loads the sit configuration.
    """
    # Arrange
    monkeypatch.setenv("APP_ENV", "sit")
    
    # Act
    import app.config
    importlib.reload(app.config)
    
    # Assert
    assert app.config.env == "sit"
    assert app.config.settings.debug_mode is False
    assert app.config.settings.log_level == "INFO"

def test_config_loading_uat(monkeypatch):
    """
    Verify that APP_ENV=uat loads the uat configuration.
    """
    # Arrange
    monkeypatch.setenv("APP_ENV", "uat")
    
    # Act
    import app.config
    importlib.reload(app.config)
    
    # Assert
    assert app.config.env == "uat"
    assert app.config.settings.debug_mode is False
    assert app.config.settings.log_level == "WARNING"

def test_config_loading_unknown_fallback(monkeypatch):
    """
    Verify that an unknown environment falls back to local configuration.
    """
    # Arrange
    monkeypatch.setenv("APP_ENV", "unknown-env-name")
    
    # Act
    import app.config
    importlib.reload(app.config)
    
    # Assert
    assert app.config.env == "unknown-env-name"
    assert app.config.settings.log_level == "DEBUG"

