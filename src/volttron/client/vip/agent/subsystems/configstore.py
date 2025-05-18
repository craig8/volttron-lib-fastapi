# src/volttron/client/vip/agent/subsystems/configstore.py
"""ConfigStore subsystem for VIP agents."""
import logging

_log = logging.getLogger(__name__)

class ConfigStore:
    """ConfigStore subsystem for VIP agents."""
    
    def __init__(self, owner=None, core=None, rpc=None):
        """Initialize the ConfigStore subsystem."""
        self.owner = owner
        self.core = core
        self.rpc = rpc