import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.utils.tracing import request_id
from app.utils import metrics
import time
import io

VALID_IMAGE_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\x0bIDAT\x08\x99c\xf8\x0f\x04\x00\x09\xfb"
    b"\x03\xfd\xe3U\xf2\x9c\x00\x00\x00\x00IEND\xaeB`\x82"
)

@pytest.fixture
def test_client():
    # Make sure metrics and tracing are enabled for tests
    settings.enable_metrics = True
    settings.enable_request_tracing = True
    
    metrics.ACTIVE_REQUESTS.set(0)
    metrics.ACTIVE_INFERENCES.set(0)
    metrics.QUEUED_INFERENCES.set(0)
    
    with TestClient(app) as client:
        yield client

def test_request_id_generation(test_client):
    """Verify that a Request-ID is generated and returned if not provided."""
    res = test_client.get("/health")
    assert res.status_code == 200
    assert "X-Request-ID" in res.headers
    assert len(res.headers["X-Request-ID"]) > 10

def test_request_id_propagation(test_client):
    """Verify that an provided X-Request-ID is preserved and returned."""
    custom_id = "test-custom-id-123"
    res = test_client.get("/health", headers={"X-Request-ID": custom_id})
    assert res.status_code == 200
    assert res.headers["X-Request-ID"] == custom_id

def test_metrics_endpoint(test_client):
    """Verify that the /metrics endpoint exposes Prometheus format data."""
    # First make a request to generate some metrics
    test_client.get("/health")
    
    res = test_client.get("/metrics")
    assert res.status_code == 200
    content = res.text
    
    # Check that our custom metrics are present in the output
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
    assert "active_requests" in content

def test_inference_metrics_recorded(test_client, mocker):
    """Verify that segmentation metrics are recorded properly."""
    mocker.patch("app.routes.segmentation.run_segmentation")
    mocker.patch("app.routes.segmentation.generate_secure_path", return_value="dummy_path.png")
    mocker.patch("app.routes.segmentation.FileResponse", return_value={"status": "ok"})
    
    app.state.model = "dummy_model"
    app.state.inference_semaphore = asyncio.Semaphore(10)
    app.state.active_inferences = 0
    app.state.queued_inferences = 0
    
    res = test_client.post("/segment", files={"file": ("test.png", io.BytesIO(VALID_IMAGE_BYTES), "image/png")})
    assert res.status_code == 200
    
    metrics_res = test_client.get("/metrics")
    content = metrics_res.text
    
    # We should have observed inference duration
    assert "yolo_inference_duration_seconds" in content

def test_rate_limit_metrics(test_client, mocker):
    """Verify that rate limit violations are tracked in Prometheus."""
    from app.utils.rate_limit import rate_limit_records
    rate_limit_records.clear()
    
    mocker.patch.object(settings, "rate_limit_requests", 0)  # Always rate limit
    
    res = test_client.get("/health") # health isn't rate limited
    
    app.state.model = "dummy_model"
    app.state.inference_semaphore = asyncio.Semaphore(10)
    app.state.active_inferences = 0
    app.state.queued_inferences = 0
    
    res = test_client.post("/segment", files={"file": ("test.png", io.BytesIO(VALID_IMAGE_BYTES), "image/png")})
    assert res.status_code == 429
    
    metrics_res = test_client.get("/metrics")
    assert "http_rate_limit_violations_total" in metrics_res.text
