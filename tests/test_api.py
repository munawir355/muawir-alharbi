import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.main import app
from app.config import get_settings, Settings
from app.auth_service import AuthUtils


# Test settings
@pytest.fixture
def test_settings():
    return Settings(
        DEBUG=True,
        SECRET_KEY="test-secret-key",
        DB_SERVER="test-server",
        DB_NAME="test-db"
    )


# Override settings for testing
@pytest.fixture
def app_client(test_settings):
    # Override get_settings to return test settings
    app.dependency_overrides[get_settings] = lambda: test_settings
    return TestClient(app)


# Mock database connection
@pytest.fixture
def mock_db():
    mock = MagicMock()
    mock.cursor = MagicMock()
    return mock


# Mock authenticated user
@pytest.fixture
def auth_headers():
    token = AuthUtils.create_access_token(
        data={"sub": "test@plymouth.ac.uk", "user_id": 1}
    )
    return {"Authorization": f"Bearer {token}"}


# Test cases
def test_read_main(app_client):
    """Test root endpoint"""
    response = app_client.get("/")
    assert response.status_code == 200
    assert "Trail Service API" in response.json()["title"]


def test_login(app_client, mock_db):
    """Test login endpoint"""
    # Mock Plymouth authentication
    with patch('app.auth_utils.AuthUtils.verify_plymouth_credentials', return_value=True):
        # Mock database user retrieval
        mock_db.cursor().fetchone.return_value = (1, "Test User", "test@plymouth.ac.uk")

        response = app_client.post(
            "/token",
            data={"username": "test@plymouth.ac.uk", "password": "password"}
        )

        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "token_type" in response.json()


def test_create_trail(app_client, mock_db, auth_headers):
    """Test trail creation"""
    # Mock database operations
    mock_db.cursor().fetchone.return_value = (
        1, "Test Trail", "Test Description", datetime.now(), 1
    )

    response = app_client.post(
        "/api/trails",
        json={
            "TrailName": "Test Trail",
            "Description": "Test Description"
        },
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["TrailName"] == "Test Trail"


def test_get_trails(app_client, mock_db):
    """Test getting all trails"""
    # Mock database response
    mock_trails = [
        (1, "Trail 1", "Description 1", datetime.now(), 1),
        (2, "Trail 2", "Description 2", datetime.now(), 1)
    ]
    mock_db.cursor().fetchall.return_value = mock_trails

    response = app_client.get("/api/trails")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_update_trail(app_client, mock_db, auth_headers):
    """Test trail update"""
    # Mock existing trail check
    mock_db.cursor().fetchone.return_value = (1,)  # CreatedBy user_id

    response = app_client.put(
        "/api/trails/1",
        json={
            "TrailName": "Updated Trail",
            "Description": "Updated Description"
        },
        headers=auth_headers
    )

    assert response.status_code == 200


def test_delete_trail(app_client, mock_db, auth_headers):
    """Test trail deletion"""
    # Mock existing trail check
    mock_db.cursor().fetchone.return_value = (1,)  # CreatedBy user_id

    response = app_client.delete(
        "/api/trails/1",
        headers=auth_headers
    )

    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]


def test_unauthorized_access(app_client):
    """Test unauthorized access"""
    response = app_client.get("/api/trails/1")
    assert response.status_code == 401


def test_invalid_trail_id(app_client, mock_db, auth_headers):
    """Test invalid trail ID"""
    mock_db.cursor().fetchone.return_value = None

    response = app_client.get(
        "/api/trails/999",
        headers=auth_headers
    )

    assert response.status_code == 404
