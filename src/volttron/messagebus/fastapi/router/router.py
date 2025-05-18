"""
Message router for the VOLTTRON FastAPI messagebus.
"""
import asyncio
import logging
from typing import Dict, Set, List, Any, Optional

from fastapi import WebSocket

_log = logging.getLogger(__name__)

class MessageRouter:
    """
    Routes messages between agents in the VOLTTRON messagebus.
    """
    
    def __init__(self):
        """Initialize the message router."""
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> set of subscriber ids
        self.connections: Dict[str, WebSocket] = {}  # agent_id -> websocket
        
    def register_agent(self, agent_id: str, websocket: WebSocket):
        """
        Register an agent connection with the router.
        
        Args:
            agent_id: The ID of the agent
            websocket: The WebSocket connection for the agent
        """
        self.connections[agent_id] = websocket
        _log.info(f"Registered agent {agent_id} with router")
        
    def unregister_agent(self, agent_id: str):
        """
        Unregister an agent connection from the router.
        
        Args:
            agent_id: The ID of the agent to unregister
        """
        if agent_id in self.connections:
            del self.connections[agent_id]
            
        # Remove from subscriptions
        for topic, subscribers in list(self.subscriptions.items()):
            if agent_id in subscribers:
                subscribers.remove(agent_id)
                if not subscribers:
                    del self.subscriptions[topic]
                    
        _log.info(f"Unregistered agent {agent_id} from router")
        
    def subscribe(self, topic: str, agent_id: str):
        """
        Subscribe an agent to a topic.
        
        Args:
            topic: The topic to subscribe to
            agent_id: The ID of the subscribing agent
        """
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        self.subscriptions[topic].add(agent_id)
        _log.info(f"Agent {agent_id} subscribed to topic {topic}")
        
    async def publish(self, topic: str, data: Any, sender_id: str):
        """
        Publish a message to a topic.
        
        Args:
            topic: The topic to publish to
            data: The data to publish
            sender_id: The ID of the sending agent
        """
        subscribers = self.subscriptions.get(topic, set())
        
        # Create the message envelope
        envelope = {
            "type": "message",
            "topic": topic,
            "sender": sender_id,
            "data": data
        }
        
        # Send to all subscribers except the sender
        for subscriber_id in subscribers:
            if subscriber_id != sender_id and subscriber_id in self.connections:
                try:
                    await self.connections[subscriber_id].send_json(envelope)
                    _log.debug(f"Sent message from {sender_id} to {subscriber_id} on topic {topic}")
                except Exception as e:
                    _log.error(f"Failed to send message to {subscriber_id}: {e}")
                    
        _log.info(f"Published message from {sender_id} to {len(subscribers)} subscribers on topic {topic}")
        
    async def route_rpc(self, target_agent: str, method: str, params: Any, 
                 req_id: str, sender_id: str) -> bool:
        """
        Route an RPC request to the target agent.
        
        Args:
            target_agent: The ID of the target agent
            method: The method to call
            params: The parameters to pass
            req_id: The request ID for correlation
            sender_id: The ID of the sending agent
            
        Returns:
            True if the message was routed successfully, False otherwise
        """
        if target_agent not in self.connections:
            _log.error(f"Cannot route RPC to unknown agent {target_agent}")
            return False
        
        # Create the RPC request message
        message = {
            "type": "rpc",
            "id": req_id,
            "method": method,
            "params": params,
            "sender": sender_id
        }
        
        _log.info(f"Routing RPC: {sender_id} -> {target_agent}.{method} (ID: {req_id})")
        
        try:
            # Send the RPC request to the target agent
            await self.connections[target_agent].send_json(message)
            _log.debug(f"Routed RPC call from {sender_id} to {target_agent}.{method}")
            return True
        except Exception as e:
            _log.error(f"Failed to route RPC to {target_agent}: {e}")
            return False