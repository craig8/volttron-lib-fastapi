# src/volttron/messagebus/fastapi/core/base.py
"""
Base interface for the core message processing loop.
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Set, Union

class BaseCoreLoop(ABC):
    """
    Abstract base class defining the interface for CoreLoop implementations.
    
    This defines a common interface that both AsyncCoreLoop and 
    GeventCoreLoop will implement, without specifying the concurrency model.
    """
    
    def __init__(self, agent_id: str, websocket):
        """
        Initialize the core loop for an agent connection.
        
        Args:
            agent_id: The ID of the connecting agent
            websocket: The websocket connection for the agent
        """
        self.agent_id = agent_id
        self.websocket = websocket
        self.running = False
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> set of subscriber ids
        self.rpc_methods: Dict[str, Callable] = {}
    
    @abstractmethod
    def start(self):
        """Start the core loop processing."""
        pass
        
    @abstractmethod
    def stop(self):
        """Stop the core loop processing."""
        pass
        
    @abstractmethod
    def handle_message(self, message: dict) -> Optional[dict]:
        """
        Process an incoming message from the agent.
        
        Args:
            message: The parsed JSON message from the agent
        
        Returns:
            Optional response to send back to the agent
        """
        pass
        
    @abstractmethod
    def handle_rpc_request(self, message: dict) -> dict:
        """Handle an RPC request message."""
        pass
        
    @abstractmethod
    def handle_rpc_response(self, message: dict) -> Optional[dict]:
        """Handle an RPC response message."""
        pass
            
    @abstractmethod
    def handle_subscribe(self, message: dict) -> dict:
        """Handle a topic subscription request."""
        pass
            
    @abstractmethod
    def handle_publish(self, message: dict) -> dict:
        """Handle a message publication."""
        pass
        
    @abstractmethod
    def call_rpc(self, target_agent: str, method: str, params: list = None) -> Any:
        """
        Call an RPC method on another agent.
        
        Args:
            target_agent: The ID of the agent to call
            method: The method name to call
            params: The parameters to pass to the method
            
        Returns:
            The result of the RPC call
        """
        pass