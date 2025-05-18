# src/volttron/client/vip/agent/subsystems/auth.py
"""Auth subsystem for VIP agents."""
import logging

_log = logging.getLogger(__name__)

class Auth:
    """Auth subsystem for VIP agents."""
    
    def __init__(self, owner=None, core=None, rpc=None):
        """Initialize the Auth subsystem."""
        self.owner = owner
        self.core = core
        self.rpc = rpc