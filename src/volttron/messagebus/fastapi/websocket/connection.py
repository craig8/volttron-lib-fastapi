"""
WebSocket connection handler for VOLTTRON messagebus.
"""
import json
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

_log = logging.getLogger(__name__)

router = APIRouter()

# Store connected clients
connected_clients: Dict[str, WebSocket] = {}

@router.websocket("/messagebus/v1/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint for VOLTTRON agents to connect to the messagebus.
    
    Args:
        websocket: The WebSocket connection
        agent_id: The ID of the connecting agent
    """
    # Check for duplicate connection before accepting
    if agent_id in connected_clients:
        # If agent_id already exists, reject the connection
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    # Accept the connection
    await websocket.accept()
    
    try:
        connected_clients[agent_id] = websocket
        _log.info(f"Agent {agent_id} connected. Total connected: {len(connected_clients)}")
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection_established",
            "agent_id": agent_id,
            "server_id": "volttron.messagebus.fastapi"
        })
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                _log.debug(f"Received message from {agent_id}: {message}")
                
                # Process message based on its type
                message_type = message.get("type")
                if message_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "id": message.get("id")
                    })
                elif message_type == "rpc":
                    # TO DO: Implement RPC handling
                    await handle_rpc(agent_id, message, websocket)
                else:
                    await websocket.send_json({
                        "type": "error",
                        "error": f"Unsupported message type: {message_type}"
                    })
                    
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "error": "Invalid JSON message"
                })
    except WebSocketDisconnect:
        _log.info(f"Agent {agent_id} disconnected")
    finally:
        # Remove the client from connected clients
        if agent_id in connected_clients:
            del connected_clients[agent_id]
            _log.info(f"Agent {agent_id} removed. Total connected: {len(connected_clients)}")

async def handle_rpc(sender_id: str, message: dict, websocket: WebSocket):
    """Handle RPC messages between agents."""
    # For now, just echo back the RPC request
    await websocket.send_json({
        "type": "rpc_response",
        "id": message.get("id"),
        "result": f"Received RPC request: {message.get('method')}"
    })
    # TO DO: Implement actual RPC routing between agents