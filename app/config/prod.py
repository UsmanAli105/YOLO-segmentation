from app.config.base import Settings as BaseSettings

class ProdSettings(BaseSettings):
    """
    Configuration overrides for the 'prod' environment.
    """
    debug_mode: bool = False
    log_level: str = "ERROR"
    reload: bool = False
    
    # Hide/disable docs in production
    swagger_enabled: bool = False
    redoc_enabled: bool = False
    enable_openapi: bool = False
    docs_url: str = ""
    redoc_url: str = ""
