# tests/utils.py
"""
Shared utilities for testing the FastAPI messagebus.
"""
import json
import logging
import os
import socket
import subprocess
import sys
import time

import httpx

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
        
        # Start the server using uvicorn directly
        cmd = [
            python_executable, "-m", "uvicorn",
            "volttron.messagebus.fastapi.server.app:create_app",
            "--factory", "--host", self.host, "--port", str(self.port),
            "--log-level", "debug"
        ]
        
        # Start the server in a subprocess
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Wait for the server to start
        health_check_url = f"{self.http_url}/"
        for _ in range(20):  # Try for up to 10 seconds
            time.sleep(0.5)
            try:
                with httpx.Client(timeout=1.0) as client:
                    response = client.get(health_check_url)
                    if response.status_code == 200:
                        _log.info(f"Server is up on {self.host}:{self.port}")
                        return True
            except (httpx.RequestError, ConnectionRefusedError):
                _log.debug("Server not yet responsive, waiting...")
        
        _log.error(f"Server failed to start on {self.host}:{self.port}")
        # Capture any output from the server for debugging
        self.stop()
        return False
        
    def stop(self):
        """Stop the test server."""
        _log.info("Stopping test server...")
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                _log.info("Server process terminated")
                
                # Log any output for debugging
                stdout, stderr = self.process.stdout.read(), self.process.stderr.read()
                _log.debug(f"Server stdout: {stdout}")
                _log.debug(f"Server stderr: {stderr}")
            except subprocess.TimeoutExpired:
                _log.warning("Server didn't terminate, killing process")
                self.process.kill()
                self.process.wait()