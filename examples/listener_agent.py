# examples/listener_agent.py
"""
Simple listener agent using FastAPI messagebus.
"""
import logging
import os
import sys
import uuid
import gevent
from gevent import monkey

# Apply monkey patch only in the agent - not in the server
monkey.patch_all()

# Setup logging
logging.basicConfig(level=logging.DEBUG)
_log = logging.getLogger(__name__)

# Import volttron agent
from volttron.client.vip.agent import Agent, Core, PubSub
from volttron.client.messaging.health import STATUS_GOOD
from volttron.utils.commands import vip_main
from volttron.utils import utils

__version__ = '0.1.0'

DEFAULT_MESSAGE = 'Listener Message'
DEFAULT_HEARTBEAT_PERIOD = 5

class ListenerAgent(Agent):
    """Listener agent for VOLTTRON FastAPI messagebus."""
    
    def __init__(self, config_path, **kwargs):
        """Initialize the listener agent."""
        # Set environment variables for FastAPI messagebus if not already set
        if 'VOLTTRON_MESSAGEBUS' not in os.environ:
            os.environ['VOLTTRON_MESSAGEBUS'] = 'fastapi'
        if 'VOLTTRON_SERVER' not in os.environ:
            os.environ['VOLTTRON_SERVER'] = 'ws://localhost:8000'
            
        super(ListenerAgent, self).__init__(**kwargs)
        
        # Load configuration
        self.config = utils.load_config(config_path)
        self._message = self.config.get('message', DEFAULT_MESSAGE)
        self._heartbeat_period = self.config.get('heartbeat_period', DEFAULT_HEARTBEAT_PERIOD)
        
        # Set up logging function
        log_level = self.config.get('log-level', 'INFO')
        if log_level == 'ERROR':
            self._logfn = _log.error
        elif log_level == 'WARN':
            self._logfn = _log.warn
        elif log_level == 'DEBUG':
            self._logfn = _log.debug
        else:
            self._logfn = _log.info
    
    @Core.receiver('onsetup')
    def onsetup(self, sender, **kwargs):
        """Set up the agent."""
        # Demonstrate accessing a value from the config file
        _log.info(self.config.get('message', DEFAULT_MESSAGE))
    
    @Core.receiver('onstart')
    def onstart(self, sender, **kwargs):
        """Start the agent."""
        _log.debug(f"Starting ListenerAgent version {__version__}")
        
        # Set up heartbeat
        if self._heartbeat_period != 0:
            _log.debug(f"Heartbeat starting for {self.core.identity}, published every {self._heartbeat_period}s")
            self.vip.heartbeat.start_with_period(self._heartbeat_period)
            self.vip.health.set_status(STATUS_GOOD, self._message)
            
        # Subscribe to all topics
        self.vip.pubsub.subscribe('pubsub', '', self.on_match)
    
    def on_match(self, peer, sender, bus, topic, headers, message):
        """Handle messages from the message bus."""
        self._logfn(
            "Peer: {0}, Sender: {1}:, Bus: {2}, Topic: {3}, Headers: {4}, "
            "Message: \n{5}".format(peer, sender, bus, topic, headers, message)
        )

def main():
    """Main method called by the platform."""
    try:
        vip_main(ListenerAgent, version=__version__)
    except Exception as e:
        _log.exception('unhandled exception')

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    finally:
        _log.debug("Exiting ListenerAgent")