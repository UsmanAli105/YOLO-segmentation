# YOLOv8 Instance Segmentation API (FastAPI)

A clean, modular REST API built with FastAPI and Python that performs instance segmentation on uploaded images using the pretrained Ultralytics YOLOv8 segmentation model (`yolov8n-seg.pt`).

---

## Features

- **FastAPI Framework**: High performance, easy routing, and automatic interactive Swagger documentation.
- **Pretrained YOLOv8**: Leverages `yolov8n-seg.pt` loaded once during startup using FastAPI lifespan events.
- **Robust File Validation**: Ensures uploaded files are valid images using extension matching, magic bytes signature verification, and a 10MB file size limit to prevent Denial of Service (DoS) attacks.
- **Path Traversal Protection**: Renames uploaded files to secure, randomized UUID filenames.
- **Automated Cleanup**: Deletes both input upload and output processed images via background tasks once the response is sent.
- **Logging**: Configured logger prints actions and status for all major operations.

---

## Project Structure

```text
project/
│
├── app/
│   ├── main.py                     # Initializes FastAPI, registers routes, loads YOLOv8 on lifespan startup
│   ├── routes/
│   │   └── segmentation.py         # Defines POST /segment endpoint & manages upload/processing flow
│   ├── services/
│   │   └── yolo_service.py         # Performs YOLO inference, overlays segmentation masks, saves result
│   └── utils/
│       └── file_utils.py           # Validates extension, magic bytes, checks size limits, deletes temp files
│
├── uploads/                        # Temporarily holds uploaded files before inference (auto-created)
├── outputs/                        # Temporarily holds output mask-annotated files (auto-created)
├── models/                         # Holds the downloaded yolov8n-seg.pt model (auto-created)
│
├── requirements.txt                # Package dependencies list
└── README.md                       # Setup and running instructions (this file)
```

---

## Setup & Running the Application

### 1. Prerequisites
Ensure you have **Python 3.8+** installed.

### 2. Create a Virtual Environment (Recommended)
It is recommended to run the application in a virtual environment to prevent package version conflicts:

```bash
# Create the environment
python3 -m venv venv

# Activate the environment
source venv/bin/activate
```

### 3. Install Dependencies
Install all required libraries specified in the `requirements.txt`:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the Server
The application supports environment-based configuration management. You can specify the active environment using the `APP_ENV` environment variable (defaults to `local` if not specified):

- **local**: debug mode `True`, log level `DEBUG`, reload `True`, Swagger UI `/docs` enabled.
- **dev**: debug mode `True`, log level `INFO`, reload `True`, Swagger UI `/docs` enabled.
- **sit**: debug mode `False`, log level `INFO`, reload `False`, Swagger UI `/docs` enabled.
- **uat**: debug mode `False`, log level `WARNING`, reload `False`, Swagger UI `/docs` enabled.
- **prod**: debug mode `False`, log level `ERROR`, reload `False`, Swagger UI `/docs` **disabled** for production security.

You can launch the server using the startup script (which runs the test suite first):

```bash
APP_ENV=local ./run.sh
```

Or you can run `uvicorn` directly for specific environments:

```bash
# Local environment
APP_ENV=local venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

# Dev environment
APP_ENV=dev venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001

# Production environment (disables Swagger/ReDoc docs automatically)
APP_ENV=prod venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080
```

> **Security Note:** In alignment with secure coding guidelines, the application always listens on `127.0.0.1` (localhost) rather than `0.0.0.0`.

---

## Testing the API

### Interactive API Documentation (Swagger UI)
Open your web browser and go to:
- **Swagger Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc UI:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Check Health Status
Verify the server status and ensure the model has finished loading:
```bash
curl -X GET http://127.0.0.1:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

### Segment an Image using `curl`
To perform segmentation on an image file, use the following `curl` command (replace `/path/to/your/image.jpg` with a path to a real image on your system):

```bash
curl -X POST "http://127.0.0.1:8000/segment" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/image.jpg;type=image/jpeg" \
  --output output_segmented.jpg
```

This request will upload `/path/to/your/image.jpg` to the API. The API will return the image with colored segmentation masks overlaid. The response will be saved as `output_segmented.jpg` in your current directory.
Both the uploaded file and the generated segmented file on the server will be deleted automatically after the response completes.
