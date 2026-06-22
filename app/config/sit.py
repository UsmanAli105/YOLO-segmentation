from app.config.base import Settings as BaseSettings

class SitSettings(BaseSettings):
    """
    Configuration overrides for the 'sit' environment.
    """
    debug_mode: bool = False
    log_level: str = "INFO"
    reload: bool = False
