"""
Core message processing loop for the VOLTTRON FastAPI messagebus.
"""
import asyncio
import json
import logging
import uuid
from typing import Any, Callable, Dict, Optional, Set

from ..router import router as global_router

_log = logging.getLogger(__name__)

class CoreLoop:
    """
    Core message processing loop for WebSocket connections.
    
    This class manages the processing of messages for a single WebSocket connection.
    It provides mechanisms for sending and receiving messages, handling RPC calls,
    and managing subscriptions.
    """
    
    def __init__(self, agent_id: str, websocket):
        """Initialize the core loop for an agent connection."""
        self.agent_id = agent_id
        self.websocket = websocket
        self.running = False
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> set of subscriber ids
        self.rpc_methods: Dict[str, Callable] = {}
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.router = global_router
        
    async def start(self):
        """Start the core loop processing."""
        self.running = True
        # Register with the router
        self.router.register_agent(self.agent_id, self.websocket)
        _log.info(f"Starting core loop for agent {self.agent_id}")
        
    async def stop(self):
        """Stop the core loop processing."""
        self.running = False
        # Unregister from the router
        self.router.unregister_agent(self.agent_id)
        # Clear any pending requests
        for req_id, future in self.pending_requests.items():
            if not future.done():
                future.cancel()
        self.pending_requests.clear()
        _log.info(f"Stopped core loop for agent {self.agent_id}")
        
    async def handle_message(self, message: dict):
        """
        Process an incoming message from the agent.
        
        Args:
            message: The parsed JSON message from the agent
        
        Returns:
            Optional response to send back to the agent
        """
        message_type = message.get("type", "")
        
        if message_type == "ping":
            return {
                "type": "pong",
                "id": message.get("id")
            }
        
        elif message_type == "rpc":
            return await self.handle_rpc_request(message)
        
        elif message_type == "rpc_response":
            return await self.handle_rpc_response(message)
        
        elif message_type == "subscribe":
            return await self.handle_subscribe(message)
            
        elif message_type == "publish":
            return await self.handle_publish(message)
            
        else:
            _log.warning(f"Unknown message type: {message_type}")
            return {
                "type": "error",
                "id": message.get("id"),
                "error": f"Unsupported message type: {message_type}"
            }
            
    async def handle_rpc_request(self, message: dict) -> dict:
        """Handle an RPC request message."""
        method = message.get("method")
        params = message.get("params", [])
        target = message.get("target")
        sender = message.get("sender", "unknown")
        req_id = message.get("id", str(uuid.uuid4()))
        
        _log.info(f"Handling RPC request: {method} with params {params}, target={target}, sender={sender}")
        
        # If this is meant for another agent, route it
        if target and target != self.agent_id:
            _log.info(f"Routing RPC request to {target}")
            success = await self.router.route_rpc(
                target, method, params, req_id, self.agent_id
            )
            
            if success:
                # No immediate response for routed requests
                # The response will come back through handle_rpc_response
                return None
            else:
                return {
                    "type": "error",
                    "id": req_id,
                    "error": f"Failed to route RPC request to {target}"
                }
        
        # If we are the target agent, process the RPC request
        _log.info(f"Processing RPC request for {method} locally")
        
        # For this agent, we'll just echo back the request for now
        # In a real implementation, we would call a registered method
        response = {
            "type": "rpc_response",
            "id": req_id,
            "result": f"Received RPC request for {method} with {params}",
            "target": sender,  # Set the target to the original sender
            "sender": self.agent_id  # Mark ourselves as the sender of the response
        }
        
        # If this is a direct RPC call (not routed), send the response back
        if not message.get("_routed"):
            return response
        
        # If it was routed to us, we need to route the response back
        _log.info(f"Routing RPC response back to {sender}")
        if sender in self.router.connections:
            try:
                await self.router.connections[sender].send_json(response)
                _log.debug(f"Routed RPC response to {sender}")
                return None  # No need to send a response through this connection
            except Exception as e:
                _log.error(f"Failed to route RPC response to {sender}: {e}")
                return {
                    "type": "error",
                    "id": req_id,
                    "error": f"Failed to route RPC response to {sender}"
                }
        else:
            _log.error(f"Unknown sender {sender} for RPC response")
            return {
                "type": "error",
                "id": req_id, 
                "error": f"Unknown sender {sender} for RPC response"
            }
        
    async def handle_rpc_response(self, message: dict) -> Optional[dict]:
        """Handle an RPC response message."""
        req_id = message.get("id")
        sender = message.get("sender")
        target = message.get("target")
        
        _log.info(f"Handling RPC response: ID={req_id}, target={target}, sender={sender}")
        
        # If this agent is waiting for this response, resolve the future
        if req_id in self.pending_requests:
            _log.debug(f"Found pending request {req_id}, resolving future")
            future = self.pending_requests.pop(req_id)
            if not future.done():
                future.set_result(message.get("result"))
            return None
        
        # If this is meant for another agent, route it
        if target and target != self.agent_id:
            _log.info(f"Routing RPC response to {target}")
            if target in self.router.connections:
                try:
                    await self.router.connections[target].send_json(message)
                    _log.debug(f"Routed RPC response from {self.agent_id} to {target}")
                except Exception as e:
                    _log.error(f"Failed to route RPC response to {target}: {e}")
                    return {
                        "type": "error",
                        "error": f"Failed to route RPC response to {target}"
                    }
            else:
                _log.error(f"Unknown target agent {target} for RPC response")
                return {
                    "type": "error",
                    "error": f"Unknown target agent {target} for RPC response"
                }
        
        # No response needed for an RPC response
        return None
            
    async def handle_subscribe(self, message: dict) -> dict:
        """Handle a topic subscription request."""
        topic = message.get("topic")
        if not topic:
            return {
                "type": "error",
                "id": message.get("id"),
                "error": "Missing topic in subscription request"
            }
            
        # Track the subscription locally
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        self.subscriptions[topic].add(self.agent_id)
        
        # Register with the router
        self.router.subscribe(topic, self.agent_id)
        
        _log.info(f"Agent {self.agent_id} subscribed to topic {topic}")
        
        return {
            "type": "subscribe_confirm",
            "id": message.get("id"),
            "topic": topic
        }
            
    async def handle_publish(self, message: dict) -> dict:
        """Handle a message publication."""
        topic = message.get("topic")
        data = message.get("data")
        
        if not topic:
            return {
                "type": "error",
                "id": message.get("id"),
                "error": "Missing topic in publish request"
            }
            
        _log.debug(f"Agent {self.agent_id} published to {topic}: {data}")
        
        # Forward to subscribers through the router
        await self.router.publish(topic, data, self.agent_id)
        
        return {
            "type": "publish_confirm",
            "id": message.get("id"),
            "topic": topic
        }
        
    async def call_rpc(self, target_agent: str, method: str, params: list = None) -> Any:
        """
        Call an RPC method on another agent.
        
        Args:
            target_agent: The ID of the agent to call
            method: The method name to call
            params: The parameters to pass to the method
            
        Returns:
            The result of the RPC call
        """
        if params is None:
            params = []
            
        req_id = str(uuid.uuid4())
        request = {
            "type": "rpc",
            "id": req_id,
            "target": target_agent,
            "method": method,
            "params": params,
            "sender": self.agent_id
        }
        
        # Create a future to wait for the response
        future = asyncio.get_event_loop().create_future()
        self.pending_requests[req_id] = future
        
        # Send the request
        await self.websocket.send_json(request)
        
        try:
            # Wait for the response with a timeout
            result = await asyncio.wait_for(future, timeout=10.0)
            return result
        except asyncio.TimeoutError:
            self.pending_requests.pop(req_id, None)
            raise TimeoutError(f"RPC call to {target_agent}.{method} timed out")