"""
Tests for WebSocket connection functionality.
"""
import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
import json
import asyncio

from volttron.messagebus.fastapi.server.app import create_app

@pytest.fixture
def app():
    """Create a test FastAPI application."""
    return create_app()

@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)

def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["service"] == "volttron-messagebus"

def test_websocket_connection(client):
    """Test basic WebSocket connection."""
    with client.websocket_connect("/messagebus/v1/test-agent") as websocket:
        # Check welcome message
        data = websocket.receive_json()
        assert data["type"] == "connection_established"
        assert data["agent_id"] == "test-agent"
        
        # Test ping-pong
        websocket.send_json({"type": "ping", "id": "123"})
        response = websocket.receive_json()
        assert response["type"] == "pong"
        assert response["id"] == "123"

def test_duplicate_agent_id_rejected(client):
    """Test that duplicate agent IDs are rejected."""
    with client.websocket_connect("/messagebus/v1/duplicate-agent") as websocket1:
        # First connection should be accepted
        data = websocket1.receive_json()
        assert data["type"] == "connection_established"
        
        # Second connection with same ID should be rejected
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/messagebus/v1/duplicate-agent"):
                pass

def test_invalid_message_handling(client):
    """Test handling of invalid messages."""
    with client.websocket_connect("/messagebus/v1/test-agent") as websocket:
        # Skip welcome message
        websocket.receive_json()
        
        # Send invalid JSON
        websocket.send_text("not-valid-json")
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert "Invalid JSON" in response["error"]
        
        # Send valid JSON but unsupported message type
        websocket.send_json({"type": "unsupported_type"})
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert "Unsupported message type" in response["error"]