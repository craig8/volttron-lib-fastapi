"""
WebSocket connection handler for VOLTTRON messagebus.
"""
import json
import logging
from typing import Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from ..core.loop import CoreLoop

_log = logging.getLogger(__name__)

router = APIRouter()

# Store connected clients and their core loops
connected_clients: Dict[str, WebSocket] = {}
core_loops: Dict[str, CoreLoop] = {}

@router.websocket("/messagebus/v1/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint for VOLTTRON agents to connect to the messagebus.
    
    Args:
        websocket: The WebSocket connection
        agent_id: The ID of the connecting agent
    """
    _log.info(f"WebSocket connection attempt from agent {agent_id}")
    
    try:
        # Check for duplicate connection before accepting
        if agent_id in connected_clients:
            # If agent_id already exists, reject the connection
            _log.warning(f"Rejecting duplicate connection from agent {agent_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # Accept the connection
        _log.debug(f"Accepting WebSocket connection for {agent_id}")
        await websocket.accept()
        _log.info(f"WebSocket connection accepted for {agent_id}")
        
        # Create a core loop for this connection
        core_loop = CoreLoop(agent_id, websocket)
        
        try:
            # Register the client connection
            connected_clients[agent_id] = websocket
            core_loops[agent_id] = core_loop
            
            # Start the core loop
            await core_loop.start()
            
            _log.info(f"Agent {agent_id} connected. Total connected: {len(connected_clients)}")
            
            # Send welcome message
            _log.debug(f"Sending welcome message to {agent_id}")
            await websocket.send_json({
                "type": "connection_established",
                "agent_id": agent_id,
                "server_id": "volttron.messagebus.fastapi"
            })
            _log.debug(f"Welcome message sent to {agent_id}")
            
            # Handle incoming messages
            while True:
                _log.debug(f"Waiting for message from {agent_id}")
                data = await websocket.receive_text()
                _log.debug(f"Received raw message from {agent_id}: {data}")
                
                try:
                    message = json.loads(data)
                    _log.debug(f"Parsed message from {agent_id}: {message}")
                    
                    # Process message through the core loop
                    response = await core_loop.handle_message(message)
                    
                    # Send response if needed
                    if response:
                        _log.debug(f"Sending response to {agent_id}: {response}")
                        await websocket.send_json(response)
                        _log.debug(f"Response sent to {agent_id}")
                        
                except json.JSONDecodeError:
                    _log.error(f"Invalid JSON received from {agent_id}: {data}")
                    await websocket.send_json({
                        "type": "error",
                        "error": "Invalid JSON message"
                    })
        except WebSocketDisconnect:
            _log.info(f"Agent {agent_id} disconnected")
        except Exception as e:
            _log.error(f"Error handling connection for {agent_id}: {e}")
            _log.exception(e)
    except Exception as e:
        _log.error(f"Failed to accept WebSocket connection from {agent_id}: {e}")
        _log.exception(e)
    finally:
        # Stop the core loop
        if agent_id in core_loops:
            try:
                await core_loops[agent_id].stop()
            except Exception as e:
                _log.error(f"Error stopping core loop for {agent_id}: {e}")
            del core_loops[agent_id]
            
        # Remove the client from connected clients
        if agent_id in connected_clients:
            del connected_clients[agent_id]
            _log.info(f"Agent {agent_id} removed. Total connected: {len(connected_clients)}")