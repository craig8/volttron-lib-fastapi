"""
Example VOLTTRON agent client using gevent that connects to the FastAPI messagebus.
"""
import json
import logging
import uuid
import sys
import time

# Import and monkey patch first, before any other imports
import gevent
from gevent import monkey
monkey.patch_all()

import websocket  # This will be the patched websocket by gevent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
_log = logging.getLogger(__name__)

class GeventAgent:
    """Agent using gevent for concurrency."""
    
    def __init__(self, agent_id, server_url):
        """Initialize the agent."""
        self.agent_id = agent_id
        self.server_url = server_url
        self.ws = None
        self.running = False
        self.greenlet = None
    
    def start(self):
        """Start the agent."""
        _log.info(f"Starting agent {self.agent_id}")
        self.running = True
        self.greenlet = gevent.spawn(self.run)
        return self.greenlet
        
    def stop(self):
        """Stop the agent."""
        _log.info(f"Stopping agent {self.agent_id}")
        self.running = False
        if self.ws:
            self.ws.close()
        
    def run(self):
        """Main agent loop using gevent websocket client."""
        _log.info(f"Connecting to {self.server_url} as {self.agent_id}")
        
        # Set up WebSocket callbacks
        def on_message(ws, message):
            msg = json.loads(message)
            _log.info(f"Received: {msg}")
            
            # Handle subscription confirmations
            if msg.get("type") == "subscribe_confirm":
                _log.info(f"Successfully subscribed to {msg.get('topic')}")
            
            # Handle incoming messages
            elif msg.get("type") == "message":
                _log.info(f"Got message on topic {msg.get('topic')}: {msg.get('data')}")
                
        def on_error(ws, error):
            _log.error(f"WebSocket error: {error}")
            
        def on_close(ws, close_status_code, close_reason):
            _log.info(f"WebSocket closed: {close_status_code}, {close_reason}")
            if self.running:
                _log.info("Attempting to reconnect...")
                gevent.sleep(5)
                self.connect()
                
        def on_open(ws):
            _log.info("WebSocket connection established")
            # Send a ping after connection
            self.send_ping()
            # Subscribe to a topic
            self.subscribe("test/topic")
            
        # Create WebSocket connection
        self.ws = websocket.WebSocketApp(
            self.server_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Run the WebSocket connection with gevent
        self.ws.run_forever(ping_interval=30, ping_timeout=10)
        
    def connect(self):
        """Connect or reconnect to the server."""
        if self.ws:
            self.ws.close()
        self.run()
        
    def send_ping(self):
        """Send a ping message to the server."""
        ping_id = str(uuid.uuid4())
        self.ws.send(json.dumps({
            "type": "ping", 
            "id": ping_id
        }))
        _log.info(f"Sent ping with id {ping_id}")
        
    def subscribe(self, topic):
        """Subscribe to a topic."""
        sub_id = str(uuid.uuid4())
        self.ws.send(json.dumps({
            "type": "subscribe",
            "id": sub_id,
            "topic": topic
        }))
        _log.info(f"Sent subscription request for topic {topic} with id {sub_id}")
        
    def publish(self, topic, data):
        """Publish a message to a topic."""
        pub_id = str(uuid.uuid4())
        self.ws.send(json.dumps({
            "type": "publish",
            "id": pub_id,
            "topic": topic,
            "data": data
        }))
        _log.info(f"Published to topic {topic}: {data}")
        
    def call_rpc(self, target, method, params=None):
        """Call an RPC method on another agent."""
        if params is None:
            params = []
            
        rpc_id = str(uuid.uuid4())
        self.ws.send(json.dumps({
            "type": "rpc",
            "id": rpc_id,
            "target": target,
            "method": method,
            "params": params
        }))
        _log.info(f"Called RPC {method} on {target} with params {params}")
        return rpc_id

def main():
    """Run the gevent agent."""
    agent_id = sys.argv[1] if len(sys.argv) > 1 else f"gevent-agent-{uuid.uuid4().hex[:8]}"
    server_url = sys.argv[2] if len(sys.argv) > 2 else f"ws://localhost:8000/messagebus/v1/{agent_id}"
    
    agent = GeventAgent(agent_id, server_url)
    greenlet = agent.start()
    
    try:
        # Keep the main thread running
        while True:
            gevent.sleep(1)
            if not greenlet.alive:
                _log.error("Agent greenlet died, restarting...")
                greenlet = agent.start()
    except KeyboardInterrupt:
        _log.info("Keyboard interrupt received, shutting down")
        agent.stop()
        gevent.sleep(1)  # Give the websocket time to close cleanly
        
if __name__ == "__main__":
    main()