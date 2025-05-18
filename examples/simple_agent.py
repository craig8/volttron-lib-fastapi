"""
Example VOLTTRON agent client that connects to the FastAPI messagebus.
"""
import asyncio
import json
import logging
import uuid
import websockets
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
_log = logging.getLogger(__name__)

async def run_agent(agent_id, server_url):
    """Run a simple agent that connects to the messagebus."""
    _log.info(f"Connecting to {server_url} as {agent_id}")
    
    async with websockets.connect(server_url) as websocket:
        # Wait for welcome message
        response = await websocket.recv()
        welcome = json.loads(response)
        _log.info(f"Connected: {welcome}")
        
        # Send a ping
        ping_id = str(uuid.uuid4())
        await websocket.send(json.dumps({
            "type": "ping",
            "id": ping_id
        }))
        
        # Wait for pong
        response = await websocket.recv()
        pong = json.loads(response)
        _log.info(f"Received: {pong}")
        
        # Subscribe to a topic
        sub_id = str(uuid.uuid4())
        await websocket.send(json.dumps({
            "type": "subscribe",
            "id": sub_id,
            "topic": "test/topic"
        }))
        
        # Wait for subscription confirmation
        response = await websocket.recv()
        sub_confirm = json.loads(response)
        _log.info(f"Subscription: {sub_confirm}")
        
        # Main message loop
        try:
            while True:
                # Wait for messages
                response = await websocket.recv()
                message = json.loads(response)
                _log.info(f"Received message: {message}")
                
                # Handle different message types
                if message.get("type") == "message":
                    _log.info(f"Got message on topic {message.get('topic')}: {message.get('data')}")
                
        except websockets.ConnectionClosed:
            _log.info("Connection closed")

if __name__ == "__main__":
    agent_id = sys.argv[1] if len(sys.argv) > 1 else f"agent-{uuid.uuid4()}"
    server_url = sys.argv[2] if len(sys.argv) > 2 else "ws://localhost:8000/messagebus/v1/" + agent_id
    
    asyncio.run(run_agent(agent_id, server_url))