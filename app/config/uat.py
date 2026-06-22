from app.config.base import Settings as BaseSettings

class UatSettings(BaseSettings):
    """
    Configuration overrides for the 'uat' environment.
    """
    debug_mode: bool = False
    log_level: str = "WARNING"
    reload: bool = False
