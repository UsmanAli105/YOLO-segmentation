# ─────────────────────────────────────────────────────────────
#  Stage 1: Builder
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements first (before pip upgrade)
COPY requirements.txt .

# Upgrade pip, setuptools, wheel AND install requirements all to /install
# This ensures packaging and all deps go to the same prefix
RUN python -m pip install --prefix=/install pip setuptools wheel -r requirements.txt

# Download YOLOv8 model weights
RUN mkdir -p /models && \
    curl -fsSL https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n-seg.pt \
    -o /models/yolov8n-seg.pt

# ─────────────────────────────────────────────────────────────
#  Stage 2: Production Runtime
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=prod

WORKDIR /app

# Install only the bare minimum runtime system dependencies for OpenCV and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0t64 \
    curl \
 && rm -rf /var/lib/apt/lists/* \
 && apt-get clean

# Copy compiled Python packages and CLI tools from the builder stage
COPY --from=builder /install /usr/local

# Copy the pre-downloaded YOLO model weights
COPY --from=builder /models /app/models

# Copy application source code and environment configs
COPY app/ ./app/
COPY .env.* ./

# Create runtime directories with wide permissions for local logging/temp files
RUN mkdir -p logs uploads outputs temp && \
    chmod -R 777 logs uploads outputs temp

# ── Expose port ────────────────────────────────────────────────
EXPOSE 8000

# ── Start server ───────────────────────────────────────────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
