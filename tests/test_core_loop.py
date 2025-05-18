"""
Tests for the CoreLoop message processing.
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from volttron.messagebus.fastapi.core.loop import CoreLoop

@pytest.mark.asyncio
async def test_core_loop_init():
    """Test CoreLoop initialization."""
    mock_websocket = AsyncMock()
    loop = CoreLoop("test-agent", mock_websocket)
    assert loop.agent_id == "test-agent"
    assert loop.websocket == mock_websocket
    assert not loop.running

@pytest.mark.asyncio
async def test_start_stop():
    """Test starting and stopping the core loop."""
    mock_websocket = AsyncMock()
    loop = CoreLoop("test-agent", mock_websocket)
    await loop.start()
    assert loop.running
    
    await loop.stop()
    assert not loop.running
    
@pytest.mark.asyncio
async def test_handle_ping():
    """Test handling ping messages."""
    mock_websocket = AsyncMock()
    loop = CoreLoop("test-agent", mock_websocket)
    response = await loop.handle_message({"type": "ping", "id": "123"})
    assert response["type"] == "pong"
    assert response["id"] == "123"
    
@pytest.mark.asyncio
async def test_handle_subscribe():
    """Test handling subscription messages."""
    mock_websocket = AsyncMock()
    loop = CoreLoop("test-agent", mock_websocket)
    response = await loop.handle_message({
        "type": "subscribe", 
        "id": "456", 
        "topic": "test/topic"
    })
    assert response["type"] == "subscribe_confirm"
    assert response["id"] == "456"
    assert response["topic"] == "test/topic"
    assert "test/topic" in loop.subscriptions
    assert "test-agent" in loop.subscriptions["test/topic"]