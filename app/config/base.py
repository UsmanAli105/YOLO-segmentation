from typing import Set
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Application Settings
    app_name: str = "YOLOv8 Segmentation API"
    app_description: str = "FastAPI YOLOv8 Image Instance Segmentation API"
    app_version: str = "1.0.0"
    debug_mode: bool = False
    api_prefix: str = ""
    swagger_enabled: bool = True
    redoc_enabled: bool = True

    # Server Settings
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False
    workers: int = 1

    # Logging Settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s: %(message)s"
    log_file_path: str = "app.log"
    enable_console_logging: bool = True
    enable_file_logging: bool = True
    log_dir: str = "logs"
    app_log_filename: str = "app.log"
    error_log_filename: str = "error.log"
    access_log_filename: str = "access.log"
    log_rotation_max_bytes: int = 10 * 1024 * 1024
    log_backup_count: int = 5

    # Security Settings
    max_upload_size_mb: int = 10
    allowed_extensions: Set[str] = {".png", ".jpg", ".jpeg", ".webp"}
    allowed_magic_signatures: Set[str] = {"png", "jpeg", "webp"}
    request_timeout_seconds: int = 30

    # File System Settings
    uploads_directory: str = "uploads"
    outputs_directory: str = "outputs"
    models_directory: str = "models"
    temp_directory: str = "temp"

    # YOLO Model Settings
    model_name: str = "yolov8n-seg.pt"
    model_path: str = "models/yolov8n-seg.pt"
    confidence_threshold: float = 0.25
    iou_threshold: float = 0.7
    max_detections: int = 300
    inference_image_size: int = 640
    device: str = "cpu"

    # Cleanup Settings
    delete_upload_after_response: bool = True
    delete_output_after_response: bool = True
    cleanup_delay_seconds: int = 0

    # API Settings
    enable_openapi: bool = True
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"

    # Health Endpoint Settings
    health_endpoint_enabled: bool = True

    # Resilience Settings
    max_concurrent_inferences: int = 4
    max_queue_size: int = 20
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Observability Settings
    enable_metrics: bool = True
    enable_request_tracing: bool = True

    # Configuration for Pydantic Settings
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore"
    )
