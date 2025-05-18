# src/volttron/messagebus/fastapi/server/websocket.py
"""
WebSocket connection handler for VOLTTRON messagebus.
"""
import json
import logging
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

_log = logging.getLogger(__name__)

router = APIRouter()

# Track active connections
active_connections: Dict[str, WebSocket] = {}

@router.websocket("/messagebus/v1/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint for agent connections.
    
    Args:
        websocket: WebSocket connection
        agent_id: Agent ID
    """
    _log.info(f"WebSocket connection request from agent: {agent_id}")
    
    try:
        # Check for duplicate connection
        if agent_id in active_connections:
            _log.warning(f"Rejecting duplicate connection for agent: {agent_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Accept the connection
        await websocket.accept()
        _log.info(f"WebSocket connection established for agent: {agent_id}")
        
        # Register connection
        active_connections[agent_id] = websocket
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection_established",
            "agent_id": agent_id,
            "server_id": "volttron.messagebus.fastapi"
        })
        
        # Process messages
        while True:
            # Receive message
            message_text = await websocket.receive_text()
            
            try:
                # Parse message
                message = json.loads(message_text)
                _log.debug(f"Message from {agent_id}: {message}")
                
                # Process message based on type
                response = await process_message(agent_id, message)
                
                # Send response if any
                if response is not None:
                    await websocket.send_json(response)
                    
            except json.JSONDecodeError:
                # Invalid JSON
                _log.error(f"Invalid JSON from agent {agent_id}: {message_text}")
                await websocket.send_json({
                    "type": "error",
                    "error": "Invalid JSON message"
                })
                
    except WebSocketDisconnect:
        _log.info(f"Agent disconnected: {agent_id}")
        
    except Exception as e:
        _log.error(f"Error handling WebSocket connection for {agent_id}: {e}")
        
    finally:
        # Clean up
        if agent_id in active_connections:
            del active_connections[agent_id]
            
        _log.info(f"Connection cleaned up for agent: {agent_id}")

async def process_message(agent_id: str, message: dict) -> dict:
    """
    Process a message from an agent.
    
    Args:
        agent_id: Agent ID
        message: Message from the agent
        
    Returns:
        Optional response message
    """
    message_type = message.get("type", "")
    
    if message_type == "ping":
        return {
            "type": "pong",
            "id": message.get("id", "")
        }
        
    elif message_type == "vip":
        return await process_vip_message(agent_id, message)
        
    else:
        _log.warning(f"Unknown message type from {agent_id}: {message_type}")
        return {
            "type": "error",
            "error": f"Unknown message type: {message_type}"
        }

async def process_vip_message(agent_id: str, message: dict) -> dict:
    """
    Process a VIP message.
    
    Args:
        agent_id: Agent ID
        message: VIP message
        
    Returns:
        Optional response message
    """
    peer = message.get("peer", "")
    subsystem = message.get("subsystem", "")
    
    _log.debug(f"VIP message from {agent_id} to {peer}: subsystem={subsystem}")
    
    # If the message is for another agent, forward it
    if peer and peer != "" and peer in active_connections:
        try:
            # Add sender information if not present
            if "user" not in message:
                message["user"] = agent_id
                
            # Forward the message
            await active_connections[peer].send_json(message)
            return None  # No response needed
        except Exception as e:
            _log.error(f"Error forwarding VIP message to {peer}: {e}")
            return {
                "type": "error",
                "error": f"Failed to forward message to {peer}"
            }
    
    # Handle subsystem messages
    if subsystem == "pubsub":
        # Implementation for pubsub subsystem
        return await handle_pubsub(agent_id, message)
    
    # Default response for unhandled VIP messages
    return {
        "type": "error",
        "error": f"Unhandled VIP message for subsystem: {subsystem}"
    }

# Additional handler functions for different subsystems
async def handle_pubsub(agent_id: str, message: dict) -> dict:
    """Handle pubsub messages."""
    # Implementation for pubsub subsystem
    # This would need to be expanded based on your requirements
    return None  # No immediate response