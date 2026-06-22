from app.config.base import Settings as BaseSettings

class DevSettings(BaseSettings):
    """
    Configuration overrides for the 'dev' environment.
    """
    debug_mode: bool = True
    log_level: str = "INFO"
    reload: bool = True
