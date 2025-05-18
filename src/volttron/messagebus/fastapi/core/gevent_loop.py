"""
Gevent-based core loop for client-side use.
"""
import json
import logging
import uuid
from typing import Any, Callable, Dict, Optional, Set

import gevent
from gevent.event import AsyncResult

_log = logging.getLogger(__name__)

class GeventCoreLoop:
    """
    Gevent-based core message processing loop for client-side use.
    
    This class is meant to be used in gevent-based VOLTTRON agents.
    """
    
    def __init__(self, agent_id: str, websocket):
        """Initialize the core loop for an agent connection."""
        self.agent_id = agent_id
        self.websocket = websocket
        self.running = False
        self.subscriptions: Dict[str, Set[str]] = {}
        self.rpc_methods: Dict[str, Callable] = {}
        self.pending_requests: Dict[str, AsyncResult] = {}
        self.processing_greenlet = None
        
    def start(self):
        """Start the core loop processing."""
        self.running = True
        _log.info(f"Starting gevent core loop for agent {self.agent_id}")
        
        # Start message processing in a separate greenlet
        self.processing_greenlet = gevent.spawn(self._process_messages)
        
    def stop(self):
        """Stop the core loop processing."""
        self.running = False
        
        # Cancel any pending requests
        for req_id, result in self.pending_requests.items():
            if not result.ready():
                result.set_exception(Exception("CoreLoop stopped"))
        self.pending_requests.clear()
        
        # Kill the processing greenlet if it's running
        if self.processing_greenlet and not self.processing_greenlet.dead:
            self.processing_greenlet.kill()
            
        _log.info(f"Stopped gevent core loop for agent {self.agent_id}")
        
    def _process_messages(self):
        """Background greenlet to process incoming messages."""
        while self.running:
            try:
                # Implementation will depend on the websocket client used
                gevent.sleep(0.01)
            except Exception as e:
                _log.error(f"Error in message processing: {e}")