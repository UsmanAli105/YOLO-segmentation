import os
import time
import uuid
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from ultralytics import YOLO
from prometheus_client import make_asgi_app

from app.config import settings, env
from app.utils.logging_config import setup_logging
from app.utils.tracing import request_id
from app.utils import metrics
from app.routes.segmentation import router as segmentation_router

# Configure centralized root and access logging
setup_logging(settings)
logger = logging.getLogger(__name__)
access_logger = logging.getLogger("access")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage FastAPI application lifespan: load model and create folders on startup,
    and clean up resources on shutdown. All paths and configurations are derived from settings.
    """
    # 1. Print Startup Logs as required
    logger.info("========================================")
    logger.info("Application Name:   %s", settings.app_name)
    logger.info("Version:            %s", settings.app_version)
    logger.info("Active Environment: %s", env)
    logger.info("Model Path:         %s", settings.model_path)
    logger.info("Device:             %s", settings.device)
    logger.info("Log Level:          %s", settings.log_level)
    logger.info("========================================")
    
    # 2. Ensure directories exist based on configuration
    os.makedirs(settings.uploads_directory, exist_ok=True)
    os.makedirs(settings.outputs_directory, exist_ok=True)
    os.makedirs(settings.models_directory, exist_ok=True)
    os.makedirs(settings.temp_directory, exist_ok=True)
    
    logger.info("Loading YOLOv8 segmentation model from '%s'...", settings.model_path)
    try:
        # Load the pretrained model
        model = YOLO(settings.model_path)
        app.state.model = model
        logger.info("YOLOv8 model loaded successfully.")
    except Exception as e:
        logger.critical("Failed to load YOLOv8 model during startup: %s", str(e), exc_info=True)
        raise SystemExit("Application startup failed due to model loading error.") from e

    # Initialize global state for concurrency and queue management
    app.state.inference_semaphore = asyncio.Semaphore(settings.max_concurrent_inferences)
    app.state.active_inferences = 0
    app.state.queued_inferences = 0

    yield
    
    # Shutdown logic
    logger.info("FastAPI application is shutting down...")
    app.state.model = None
    logger.info("Resources cleaned up successfully.")

# Create FastAPI app with dynamic metadata and openapi settings
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url=settings.docs_url if settings.swagger_enabled else None,
    redoc_url=settings.redoc_url if settings.redoc_enabled else None,
    openapi_url="/openapi.json" if settings.enable_openapi else None,
    lifespan=lifespan
)

if settings.enable_metrics:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    """
    Extracts or generates a unique Request ID, sets it in context, 
    and appends it to the response headers.
    """
    if not settings.enable_request_tracing:
        return await call_next(request)
        
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    token = request_id.set(req_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
    finally:
        request_id.reset(token)

# Request logging middleware to track HTTP requests and log metrics to access.log
@app.middleware("http")
async def log_and_measure_requests(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path
    
    # Do not track metrics endpoint itself
    if path == "/metrics":
        return await call_next(request)
    
    if settings.enable_metrics:
        metrics.ACTIVE_REQUESTS.inc()
        
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        if settings.enable_metrics:
            metrics.REQUESTS_TOTAL.labels(method=method, endpoint=path, status_code=response.status_code).inc()
            metrics.REQUEST_DURATION.labels(method=method, endpoint=path).observe(process_time / 1000)
            
        access_logger.info(
            "%s - \"%s %s\" %d - %.2fms",
            client_ip, method, path, response.status_code, process_time
        )
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        status_code = 500
        if isinstance(e, HTTPException):
            status_code = e.status_code
            
        if settings.enable_metrics:
            metrics.REQUESTS_TOTAL.labels(method=method, endpoint=path, status_code=status_code).inc()
            metrics.REQUEST_DURATION.labels(method=method, endpoint=path).observe(process_time / 1000)
            
        access_logger.error(
            "%s - \"%s %s\" 500 (Error: %s) - %.2fms",
            client_ip, method, path, str(e), process_time
        )
        raise e
    finally:
        if settings.enable_metrics:
            metrics.ACTIVE_REQUESTS.dec()

# Register routes
app.include_router(segmentation_router, tags=["Segmentation"])

@app.get("/health", tags=["Health"], summary="Check service health")
async def health_check():
    """
    Simple health check endpoint to verify that the API and YOLOv8 model are ready.
    This can be disabled via health_endpoint_enabled settings.
    """
    if not settings.health_endpoint_enabled:
        logger.warning("Health check endpoint is disabled in settings")
        raise HTTPException(status_code=404, detail="Not Found")

    model_ready = hasattr(app.state, "model") and app.state.model is not None
    status = "healthy" if model_ready else "degraded"
    
    logger.debug("Health check requested: status=%s", status)
    
    queued = getattr(app.state, "queued_inferences", 0)
    
    return {
        "status": status,
        "model_loaded": model_ready,
        "metrics": {
            "active_inferences": getattr(app.state, "active_inferences", 0),
            "queued_inferences": queued,
            "queue_capacity_remaining": max(0, settings.max_queue_size - queued)
        }
    }
