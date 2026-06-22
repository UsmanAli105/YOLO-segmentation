# ─────────────────────────────────────────────────────────────
#  YOLOv8 Segmentation API — Production Dockerfile
#  Base: python:3.12-slim  |  Port: 8000
# ─────────────────────────────────────────────────────────────

FROM python:3.12-slim

# Keeps Python from writing .pyc files and enables real-time log output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=local

# ── System dependencies ────────────────────────────────────────
# libgl1 + libglib2.0-0 are required by OpenCV (used inside YOLOv8)
# curl is used to download model weights at build time
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0t64 \
    curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python dependencies (separate layer — cached unless requirements change) ──
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application source ─────────────────────────────────────────
COPY app/         ./app/
COPY .env.local   .env.dev   .env.sit   .env.uat   .env.prod   ./

# ── Model weights (downloaded from Ultralytics GitHub at build time) ──
RUN mkdir -p models && \
    curl -fsSL https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n-seg.pt \
    -o models/yolov8n-seg.pt

# ── Runtime directories (logs, uploads, outputs, temp) ────────
RUN mkdir -p logs uploads outputs temp

# ── Expose port ────────────────────────────────────────────────
EXPOSE 8000

# ── Start server ───────────────────────────────────────────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
