"""
Tests for the gevent-based client connection to the FastAPI messagebus.
"""
#pytestmark = pytest.mark.gevent_patched

# # Only apply monkey patch when this module is being run directly, 
# # not during discovery
# if __name__ == "__main__" or "pytest" in sys.argv and "--collect-only" not in sys.argv:
#     from gevent import monkey
#     monkey.patch_all()

from gevent import monkey
monkey.patch_all()

import pytest
import sys
import json
import logging
import os
import socket
import subprocess
import sys
import time
import uuid
from typing import Dict, List

import pytest
import httpx
import gevent
import websocket

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Use DEBUG level for more information
_log = logging.getLogger(__name__)

def find_free_port():
    """Find a free port on the system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

class ServerProcess:
    """Manages a test FastAPI server in a subprocess."""
    
    def __init__(self, host="127.0.0.1", port=None):
        self.host = host
        self.port = port or find_free_port()
        self.process = None
        self.server_url = f"ws://{host}:{self.port}"
        self.http_url = f"http://{host}:{self.port}"
        
    def start(self):
        """Start the test server in a subprocess."""
        _log.info(f"Starting test server on {self.host}:{self.port}")
        
        # Use the same Python interpreter that's running this test
        python_executable = sys.executable
        
        # Create a simple script to run the server (avoids import issues)
        server_script = f"""
import logging
logging.basicConfig(level=logging.DEBUG)
from volttron.messagebus.fastapi.server.app import create_app
import uvicorn
app = create_app()
uvicorn.run(app, host="{self.host}", port={self.port}, log_level="debug")
"""
        script_path = os.path.join(os.getcwd(), "temp_server_script.py")
        with open(script_path, "w") as f:
            f.write(server_script)
        
        try:
            # Start the server in a subprocess
            self.process = subprocess.Popen(
                [python_executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Wait for the server to start
            health_check_url = f"{self.http_url}/"
            for i in range(20):  # Try for up to 10 seconds
                time.sleep(0.5)
                try:
                    with httpx.Client(timeout=1.0) as client:
                        response = client.get(health_check_url)
                        if response.status_code == 200:
                            _log.info(f"Server is up on {self.host}:{self.port}")
                            return True
                except Exception as e:
                    _log.debug(f"Server not yet responsive (attempt {i+1}/20): {e}")
            
            _log.error(f"Server failed to start on {self.host}:{self.port}")
            # Capture any output from the server for debugging
            self.log_server_output()
            return False
        except Exception as e:
            _log.error(f"Error starting server: {e}")
            return False
        finally:
            # Clean up the temporary script
            if os.path.exists(script_path):
                os.remove(script_path)
    
    def log_server_output(self):
        """Log the server's stdout and stderr."""
        if self.process:
            stdout, stderr = self.process.communicate(timeout=1)
            _log.error(f"Server stdout: {stdout}")
            _log.error(f"Server stderr: {stderr}")
        
    def stop(self):
        """Stop the test server."""
        _log.info("Stopping test server...")
        if self.process:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                    _log.info("Server process terminated")
                except subprocess.TimeoutExpired:
                    _log.warning("Server didn't terminate, killing process")
                    self.process.kill()
                    self.process.wait(timeout=2)
                
                # Log any output for debugging
                self.log_server_output()
            except Exception as e:
                _log.error(f"Error stopping server: {e}")

class GeventClient:
    """A gevent-based WebSocket client for testing."""
    
    def __init__(self, agent_id, server_url):
        self.agent_id = agent_id
        self.server_url = server_url
        self.ws = None
        self.ws_greenlet = None
        self.callbacks = {}
        self.connected = False
        self.received_messages = []
        self.connection_error = None
        
    def start(self, wait_for_connection=True):
        """Start the client and connect to the server."""
        
        def on_message(ws, message):
            _log.debug(f"Received message: {message}")
            try:
                data = json.loads(message)
                self.received_messages.append(data)
                
                if data.get("type") == "connection_established":
                    self.connected = True
                    
                # Call message type specific callback if exists
                msg_type = data.get("type")
                if msg_type in self.callbacks:
                    self.callbacks[msg_type](data)
            except json.JSONDecodeError:
                _log.error(f"Failed to parse message as JSON: {message}")
        
        def on_error(ws, error):
            _log.error(f"WebSocket error: {error}")
            self.connection_error = error
        
        def on_close(ws, close_status_code, close_msg):
            _log.info(f"WebSocket closed: {close_status_code} - {close_msg}")
            self.connected = False
        
        def on_open(ws):
            _log.info(f"WebSocket connection opened for {self.agent_id}")
        
        # Create WebSocket connection
        ws_url = f"{self.server_url}/messagebus/v1/{self.agent_id}"
        _log.info(f"Connecting to {ws_url}")
        
        websocket.enableTrace(False)  # Set to True for verbose logging
        
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        
        # Start WebSocket in a separate greenlet
        self.ws_greenlet = gevent.spawn(lambda: self.ws.run_forever())
        
        # Wait for connection to be established
        if wait_for_connection:
            start_time = time.time()
            timeout = 10
            while not self.connected and time.time() - start_time < timeout:
                if self.connection_error:
                    raise ConnectionError(f"WebSocket connection failed: {self.connection_error}")
                gevent.sleep(0.1)
                
            if not self.connected:
                raise TimeoutError("Timed out waiting for connection to be established")
        
        return self.connected
        
    def stop(self):
        """Stop the client."""
        if self.ws:
            self.ws.close()
        if self.ws_greenlet:
            self.ws_greenlet.kill()
        self.connected = False
    
    def send_message(self, message):
        """Send a message to the server."""
        if not self.connected:
            raise ConnectionError("Not connected to server")
        
        self.ws.send(json.dumps(message))
    
    def wait_for_message(self, check_func, timeout=5):
        """Wait for a message matching the check function."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            for msg in list(self.received_messages):
                if check_func(msg):
                    return msg
            gevent.sleep(0.1)
        return None

    def clear_messages(self):
        """Clear the received messages."""
        self.received_messages.clear()

    def add_callback(self, message_type, callback):
        """Add a callback for a specific message type."""
        self.callbacks[message_type] = callback


@pytest.fixture(scope="function")
def server():
    """Start a test server for the tests."""
    test_server = ServerProcess()
    if not test_server.start():
        pytest.fail("Could not start test server")
    yield test_server
    test_server.stop()


def test_basic_connection(server):
    """Test basic WebSocket connection with a gevent client."""
    client = GeventClient("test-agent", server.server_url)
    try:
        assert client.start(), "Failed to connect to server"
        
        # Verify welcome message was received
        welcome_msg = client.wait_for_message(
            lambda msg: msg.get("type") == "connection_established"
        )
        assert welcome_msg is not None
        assert welcome_msg["agent_id"] == "test-agent"
        
    finally:
        client.stop()


def test_ping_pong(server):
    """Test ping-pong exchange with a gevent client."""
    client = GeventClient("ping-agent", server.server_url)
    try:
        assert client.start(), "Failed to connect to server"
        client.clear_messages()  # Clear welcome message
        
        # Send a ping
        ping_id = str(uuid.uuid4())
        client.send_message({
            "type": "ping", 
            "id": ping_id
        })
        
        # Wait for pong response
        pong_msg = client.wait_for_message(
            lambda msg: msg.get("type") == "pong" and msg.get("id") == ping_id
        )
        assert pong_msg is not None
        assert pong_msg["id"] == ping_id
        
    finally:
        client.stop()


def test_subscribe_topic(server):
    """Test subscribing to a topic."""
    client = GeventClient("sub-agent", server.server_url)
    try:
        assert client.start(), "Failed to connect to server"
        client.clear_messages()  # Clear welcome message
        
        # Subscribe to a topic
        sub_id = str(uuid.uuid4())
        client.send_message({
            "type": "subscribe",
            "id": sub_id,
            "topic": "test/topic"
        })
        
        # Wait for subscription confirmation
        sub_msg = client.wait_for_message(
            lambda msg: msg.get("type") == "subscribe_confirm" and msg.get("topic") == "test/topic"
        )
        assert sub_msg is not None
        assert sub_msg["topic"] == "test/topic"
        assert sub_msg["id"] == sub_id
        
    finally:
        client.stop()


def test_publish_and_subscribe(server):
    """Test publishing to a topic and receiving the message as a subscriber."""
    subscriber = GeventClient("subscriber", server.server_url)
    publisher = GeventClient("publisher", server.server_url)
    
    try:
        # Start both clients
        assert subscriber.start(), "Failed to connect subscriber"
        assert publisher.start(), "Failed to connect publisher"
        
        subscriber.clear_messages()  # Clear welcome messages
        publisher.clear_messages()
        
        # Subscribe to a topic
        test_topic = "test/pubsub"
        subscriber.send_message({
            "type": "subscribe",
            "id": str(uuid.uuid4()),
            "topic": test_topic
        })
        
        # Wait for subscription confirmation
        sub_confirm = subscriber.wait_for_message(
            lambda msg: msg.get("type") == "subscribe_confirm" and msg.get("topic") == test_topic
        )
        assert sub_confirm is not None
        
        # Give the server time to register the subscription
        gevent.sleep(0.5)
        
        # Publish a message to the topic
        test_data = {"value": 42, "timestamp": time.time()}
        publisher.send_message({
            "type": "publish",
            "id": str(uuid.uuid4()),
            "topic": test_topic,
            "data": test_data
        })
        
        # Wait for publish confirmation
        pub_confirm = publisher.wait_for_message(
            lambda msg: msg.get("type") == "publish_confirm" and msg.get("topic") == test_topic
        )
        assert pub_confirm is not None
        
        # Wait for the subscriber to receive the message
        received = subscriber.wait_for_message(
            lambda msg: msg.get("type") == "message" and msg.get("topic") == test_topic
        )
        assert received is not None
        assert received["topic"] == test_topic
        assert received["data"] == test_data
        assert received["sender"] == "publisher"  # Should match publisher's agent ID
        
    finally:
        subscriber.stop()
        publisher.stop()

def test_rpc_call(server):
    """Test basic RPC calls between agents."""
    caller = GeventClient("caller-agent", server.server_url)
    callee = GeventClient("callee-agent", server.server_url)
    
    try:
        # Start both clients
        assert caller.start(), "Failed to connect caller"
        assert callee.start(), "Failed to connect callee"
        
        caller.clear_messages()
        callee.clear_messages()
        
        # Send RPC request
        rpc_id = str(uuid.uuid4())
        caller.send_message({
            "type": "rpc",
            "id": rpc_id,
            "target": "callee-agent",
            "method": "test_method",
            "params": ["arg1", "arg2"],
            "sender": "caller-agent"  # Explicitly set sender
        })
        
        # Wait for callee to receive the RPC request
        rpc_request = callee.wait_for_message(
            lambda msg: msg.get("type") == "rpc" and msg.get("method") == "test_method"
        )
        
        assert rpc_request is not None, "Callee did not receive RPC request"
        assert rpc_request["method"] == "test_method"
        assert rpc_request["params"] == ["arg1", "arg2"]
        assert rpc_request["sender"] == "caller-agent"
        
        # Send response back
        callee.send_message({
            "type": "rpc_response",
            "id": rpc_id,
            "result": {"success": True, "value": "test-result"},
            "target": "caller-agent",
            "sender": "callee-agent"  # Explicitly set sender
        })
        
        # Wait for caller to receive the response
        rpc_response = caller.wait_for_message(
            lambda msg: msg.get("type") == "rpc_response" and msg.get("id") == rpc_id
        )
        
        assert rpc_response is not None, "Caller did not receive RPC response"
        assert rpc_response["id"] == rpc_id
        assert rpc_response["result"].get("success") is True
        assert rpc_response["result"].get("value") == "test-result"
        
    finally:
        caller.stop()

def test_connection_resilience(server):
    """Test reconnection behavior."""
    # This would require more sophisticated setup to test connection drops
    # For now, we'll just verify basic connection functionality
    client = GeventClient("reconnect-agent", server.server_url)
    
    try:
        # First connection
        assert client.start(), "Failed to connect to server"
        client.clear_messages()
        
        # Send a ping to verify connection is working
        ping_id = str(uuid.uuid4())
        client.send_message({
            "type": "ping", 
            "id": ping_id
        })
        
        response = client.wait_for_message(
            lambda msg: msg.get("type") == "pong" and msg.get("id") == ping_id
        )
        assert response is not None
        
        # Manually close connection
        client.stop()
        
        # Wait a moment
        gevent.sleep(1)
        
        # Reconnect
        assert client.start(), "Failed to reconnect to server"
        client.clear_messages()
        
        # Send another ping to verify new connection is working
        ping_id = str(uuid.uuid4())
        client.send_message({
            "type": "ping", 
            "id": ping_id
        })
        
        response = client.wait_for_message(
            lambda msg: msg.get("type") == "pong" and msg.get("id") == ping_id
        )
        assert response is not None
        
    finally:
        client.stop()


def test_multiple_clients(server):
    """Test multiple clients connecting simultaneously."""
    num_clients = 5
    clients = []
    
    try:
        # Start multiple clients
        for i in range(num_clients):
            client = GeventClient(f"multi-agent-{i}", server.server_url)
            assert client.start(), f"Failed to connect client {i}"
            clients.append(client)
        
        # Verify all clients are connected
        for i, client in enumerate(clients):
            assert client.connected, f"Client {i} not connected"
            
            # Send a ping from each client
            ping_id = str(uuid.uuid4())
            client.send_message({
                "type": "ping", 
                "id": ping_id
            })
            
            response = client.wait_for_message(
                lambda msg: msg.get("type") == "pong" and msg.get("id") == ping_id
            )
            assert response is not None, f"Client {i} did not receive pong response"
            
    finally:
        for client in clients:
            client.stop()