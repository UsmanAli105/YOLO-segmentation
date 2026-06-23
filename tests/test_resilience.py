import pytest
import asyncio
import io
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

# Sample valid image bytes for testing
VALID_IMAGE_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\x0bIDAT\x08\x99c\xf8\x0f\x04\x00\x09\xfb"
    b"\x03\xfd\xe3U\xf2\x9c\x00\x00\x00\x00IEND\xaeB`\x82"
)

@pytest.fixture
def test_client():
    with TestClient(app) as client:
        yield client

def test_rate_limiting(test_client, mocker):
    """
    Test that the IP-based rate limiter returns 429 when the limit is exceeded.
    """
    # Mock rate limit settings
    mocker.patch.object(settings, "rate_limit_requests", 2)
    mocker.patch.object(settings, "rate_limit_window_seconds", 60)
    
    # Mock inference to return a dummy file without doing actual work
    mocker.patch("app.routes.segmentation.run_segmentation")
    mocker.patch("app.routes.segmentation.generate_secure_path", return_value="dummy_path.png")
    mocker.patch("app.routes.segmentation.FileResponse", return_value={"status": "ok"})
    
    # We need to mock the state model check
    app.state.model = "dummy_model"
    app.state.inference_semaphore = asyncio.Semaphore(10)
    app.state.active_inferences = 0
    app.state.queued_inferences = 0
    
    file_payload = {"file": ("test.png", io.BytesIO(VALID_IMAGE_BYTES), "image/png")}
    
    # Request 1: Should pass
    res1 = test_client.post("/segment", files={"file": ("test.png", io.BytesIO(VALID_IMAGE_BYTES), "image/png")})
    assert res1.status_code == 200
    
    # Request 2: Should pass
    res2 = test_client.post("/segment", files={"file": ("test.png", io.BytesIO(VALID_IMAGE_BYTES), "image/png")})
    assert res2.status_code == 200
    
    # Request 3: Should fail with 429
    res3 = test_client.post("/segment", files={"file": ("test.png", io.BytesIO(VALID_IMAGE_BYTES), "image/png")})
    assert res3.status_code == 429
    assert "Too Many Requests" in res3.json()["detail"]

def test_queue_capacity_limit(test_client, mocker):
    """
    Test that the API returns 503 when the queue is full.
    """
    mocker.patch.object(settings, "max_queue_size", 0)  # Queue size 0 means no waiting allowed
    mocker.patch.object(settings, "rate_limit_requests", 100)
    
    mocker.patch("app.routes.segmentation.run_segmentation")
    mocker.patch("app.routes.segmentation.generate_secure_path", return_value="dummy_path.png")
    
    app.state.model = "dummy_model"
    # Semaphore is 0, so any attempt to acquire will block/queue
    app.state.inference_semaphore = asyncio.Semaphore(0)
    app.state.active_inferences = 4
    app.state.queued_inferences = 0  # We set queue capacity to 0
    
    res = test_client.post("/segment", files={"file": ("test.png", io.BytesIO(VALID_IMAGE_BYTES), "image/png")})
    assert res.status_code == 503
    assert "queue full" in res.json()["detail"].lower() or "high load" in res.json()["detail"].lower()

def test_health_metrics(test_client):
    """
    Test that the health endpoint exposes the correct metrics.
    """
    app.state.active_inferences = 2
    app.state.queued_inferences = 5
    settings.max_queue_size = 20
    
    res = test_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert data["metrics"]["active_inferences"] == 2
    assert data["metrics"]["queued_inferences"] == 5
    assert data["metrics"]["queue_capacity_remaining"] == 15
