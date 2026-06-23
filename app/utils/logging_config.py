import os
import logging
from logging.handlers import RotatingFileHandler
from app.utils.tracing import request_id

class RequestIdFilter(logging.Filter):
    """Injects the current request_id into log records."""
    def filter(self, record):
        record.request_id = request_id.get()
        return True

def setup_logging(settings) -> None:
    """
    Configure centralized root logging and access logging with rotating file handlers
    according to settings configuration.
    """
    # 1. Create logs directory if it does not exist
    os.makedirs(settings.log_dir, exist_ok=True)
    
    # Get root logger and reset its handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    # Configure root log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Formatter for application logs
    formatter = logging.Formatter(settings.log_format)
    request_filter = RequestIdFilter()
    
    # 2. Add root console handler
    if settings.enable_console_logging:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        console_handler.addFilter(request_filter)
        root_logger.addHandler(console_handler)
        
    # 3. Add root rotating file handlers
    if settings.enable_file_logging:
        # app.log for general logs (INFO/DEBUG and up)
        app_log_path = os.path.join(settings.log_dir, settings.app_log_filename)
        app_handler = RotatingFileHandler(
            app_log_path,
            maxBytes=settings.log_rotation_max_bytes,
            backupCount=settings.log_backup_count
        )
        app_handler.setFormatter(formatter)
        app_handler.setLevel(log_level)
        app_handler.addFilter(request_filter)
        root_logger.addHandler(app_handler)
        
        # error.log for error logs only (ERROR and CRITICAL)
        error_log_path = os.path.join(settings.log_dir, settings.error_log_filename)
        error_handler = RotatingFileHandler(
            error_log_path,
            maxBytes=settings.log_rotation_max_bytes,
            backupCount=settings.log_backup_count
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        error_handler.addFilter(request_filter)
        root_logger.addHandler(error_handler)
        
    # 4. Setup dedicated access logger
    access_logger = logging.getLogger("access")
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False  # Prevent access logs from propagating to root handlers (app.log/error.log)
    
    # Reset access handlers
    for handler in access_logger.handlers[:]:
        access_logger.removeHandler(handler)
        
    # Formatter for access logs (timestamp and message)
    access_formatter = logging.Formatter("%(asctime)s [%(request_id)s] - %(message)s")
    
    if settings.enable_console_logging:
        access_console = logging.StreamHandler()
        access_console.setFormatter(access_formatter)
        access_console.setLevel(logging.INFO)
        access_console.addFilter(request_filter)
        access_logger.addHandler(access_console)
        
    if settings.enable_file_logging:
        access_log_path = os.path.join(settings.log_dir, settings.access_log_filename)
        access_file_handler = RotatingFileHandler(
            access_log_path,
            maxBytes=settings.log_rotation_max_bytes,
            backupCount=settings.log_backup_count
        )
        access_file_handler.setFormatter(access_formatter)
        access_file_handler.setLevel(logging.INFO)
        access_file_handler.addFilter(request_filter)
        access_logger.addHandler(access_file_handler)
