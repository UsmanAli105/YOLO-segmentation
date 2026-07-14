from app.config.base import Settings as BaseSettings

class ProdSettings(BaseSettings):
    """
    Configuration overrides for the 'prod' environment.
    """
    debug_mode: bool = False
    log_level: str = "ERROR"
    reload: bool = False
    
    # Enable docs in production for API documentation
    swagger_enabled: bool = True
    redoc_enabled: bool = True
    enable_openapi: bool = True
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
