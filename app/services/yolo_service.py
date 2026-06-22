import os
import logging
from PIL import Image
from ultralytics import YOLO
from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

def run_segmentation(model: YOLO, input_path: str, output_path: str) -> None:
    """
    Run YOLOv8 instance segmentation on an input image and save the result with masks overlaid.
    Uses settings for inference thresholds, device, image size, and max detections.
    """
    logger.info("Starting YOLOv8 instance segmentation on: %s", input_path)
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input image not found: {input_path}")
        
    try:
        # Run inference using configurable thresholds and parameters
        results = model(
            input_path,
            conf=settings.confidence_threshold,
            iou=settings.iou_threshold,
            max_det=settings.max_detections,
            imgsz=settings.inference_image_size,
            device=settings.device
        )
        
        if not results:
            raise ValueError("No results returned from the YOLO model.")
            
        # Get the first result (single image input)
        result = results[0]
        
        # Plot predictions (labels, bounding boxes, and colored segmentation masks)
        # plot() returns a numpy array in BGR format
        plotted_bgr = result.plot()
        
        # Convert BGR (OpenCV) to RGB (PIL)
        plotted_rgb = plotted_bgr[..., ::-1]
        
        # Save the image
        img = Image.fromarray(plotted_rgb)
        img.save(output_path)
        logger.info("Successfully saved segmented output to: %s", output_path)
        
    except Exception as e:
        logger.error("Error during YOLO segmentation processing: %s", str(e))
        raise RuntimeError(f"YOLO segmentation failed: {str(e)}")
