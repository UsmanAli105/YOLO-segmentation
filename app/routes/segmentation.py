import os
import asyncio
import logging
from fastapi import APIRouter, UploadFile, File, Request, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse

from app.config import settings
from app.utils.file_utils import (
    validate_image_extension,
    validate_image_content,
    generate_secure_path,
    cleanup_file,
)
from app.utils.rate_limit import check_rate_limit
from app.services.yolo_service import run_segmentation

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/segment", 
    summary="Perform YOLOv8 instance segmentation on an uploaded image",
    dependencies=[Depends(check_rate_limit)]
)
async def segment_image(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="The image file to segment")
):
    """
    Accepts an image file, runs YOLOv8 instance segmentation to detect objects,
    overlays colored segmentation masks, and returns the annotated image.
    All temporary files are securely validated, processed, and deleted after response delivery.
    """
    logger.info("Received request to segment image: filename=%s", file.filename)

    # 1. Validate file extension
    if not file.filename or not validate_image_extension(file.filename):
        logger.warning("Rejected file upload: invalid extension in filename='%s'", file.filename)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension. Allowed extensions are: {', '.join(sorted(settings.allowed_extensions))}"
        )

    input_path = None
    output_path = None

    try:
        # 2. Read file in chunks to enforce size limit and prevent memory exhaustion (DoS)
        contents = b""
        chunk_size = 8192  # 8KB chunks
        max_size = settings.max_upload_size_mb * 1024 * 1024
        while chunk := await file.read(chunk_size):
            contents += chunk
            if len(contents) > max_size:
                logger.warning("Rejected file upload: file size exceeds limit of %dMB", settings.max_upload_size_mb)
                raise HTTPException(
                    status_code=413,
                    detail=f"File size exceeds the maximum limit of {settings.max_upload_size_mb}MB."
                )

        # 3. Validate image magic bytes
        if not validate_image_content(contents):
            logger.warning("Rejected file upload: invalid image magic bytes signature")
            raise HTTPException(
                status_code=400,
                detail="Invalid image content. File signature check failed."
            )

        # Get file extension for output consistency
        _, ext = os.path.splitext(file.filename.lower())

        # 4. Generate secure paths and write the temporary file
        input_path = generate_secure_path(settings.uploads_directory, ext)
        output_path = generate_secure_path(settings.outputs_directory, ext)

        with open(input_path, "wb") as f:
            f.write(contents)
        logger.info("Saved raw upload temporarily to: %s", input_path)

        # 5. Retrieve pre-loaded YOLO model from app state
        if not hasattr(request.app.state, "model") or request.app.state.model is None:
            logger.error("YOLO model not loaded in application state")
            raise HTTPException(
                status_code=500,
                detail="Model service is currently unavailable."
            )

        model = request.app.state.model

        # 6. Check queue capacity and run segmentation using concurrency limits
        semaphore = request.app.state.inference_semaphore
        
        # Check if the queue is full before waiting
        if request.app.state.queued_inferences >= settings.max_queue_size:
            logger.warning("Rejected file upload: server is too busy (queue full).")
            raise HTTPException(
                status_code=503,
                detail="The server is currently experiencing high load. Please try again later."
            )
            
        request.app.state.queued_inferences += 1
        try:
            # Wait for an available concurrency slot
            async with semaphore:
                request.app.state.queued_inferences -= 1
                request.app.state.active_inferences += 1
                try:
                    logger.debug("Starting background thread for inference.")
                    # Run inference in a threadpool to avoid blocking the main event loop
                    await asyncio.to_thread(run_segmentation, model, input_path, output_path)
                finally:
                    request.app.state.active_inferences -= 1
        except Exception:
            # If an error happens while waiting for semaphore, we need to decrement the queue
            if request.app.state.queued_inferences > 0:
                request.app.state.queued_inferences -= 1
            raise

        # 7. Schedule files for deletion after the response is completed based on settings
        if settings.delete_upload_after_response:
            background_tasks.add_task(cleanup_file, input_path)
        if settings.delete_output_after_response:
            background_tasks.add_task(cleanup_file, output_path)

        # Map correct media type
        media_type = "image/jpeg" if ext in (".jpg", ".jpeg") else f"image/{ext.lstrip('.')}"

        logger.info("Returning segmented image file response")
        return FileResponse(
            path=output_path,
            media_type=media_type,
            background=background_tasks
        )

    except HTTPException:
        # Re-raise HTTP exceptions to let FastAPI handle them
        if input_path and settings.delete_upload_after_response:
            cleanup_file(input_path)
        if output_path and settings.delete_output_after_response:
            cleanup_file(output_path)
        raise
    except Exception as e:
        logger.error("Unexpected error in /segment route: %s", str(e), exc_info=True)
        if input_path and settings.delete_upload_after_response:
            cleanup_file(input_path)
        if output_path and settings.delete_output_after_response:
            cleanup_file(output_path)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the image."
        )
