# src/volttron/client/vip/agent/subsystems/hello.py
"""Hello subsystem for VIP agents."""
import logging

_log = logging.getLogger(__name__)

class Hello:
    """Hello subsystem for VIP agents."""
    
    def __init__(self, core=None):
        """Initialize the Hello subsystem."""
        self.core = core