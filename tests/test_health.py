def test_health_check_endpoint(client):
    """
    Test that the GET /health endpoint returns HTTP 200, is healthy, 
    and indicates the YOLOv8 model is loaded.
    """
    # Arrange (Implicitly handled by client fixture)

    # Act: Request the health status
    response = client.get("/health")

    # Assert: Verify response details
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True

def test_health_check_endpoint_disabled(client):
    """
    Verify that disabling the health endpoint in settings causes GET /health to return 404.
    """
    # Arrange: Disable the health endpoint on the settings instance used by app.main
    import app.main
    app.main.settings.health_endpoint_enabled = False

    try:
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Not Found"
    finally:
        # Restore configuration
        app.main.settings.health_endpoint_enabled = True

