from app.config.base import Settings as BaseSettings

class LocalSettings(BaseSettings):
    """
    Configuration overrides for the 'local' environment.
    """
    debug_mode: bool = True
    log_level: str = "DEBUG"
    reload: bool = True
