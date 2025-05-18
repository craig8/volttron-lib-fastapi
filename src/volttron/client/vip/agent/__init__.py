"""VIP agent implementation for FastAPI messagebus."""
from __future__ import annotations
import os
from typing import Optional

from volttron.types import AbstractAgent
from volttron.types.auth.auth_credentials import Credentials
from volttron.types.agent_context import AgentContext, AgentOptions
from volttron.utils import get_logger

from .core import Core
from .decorators import *
from .errors import *
from .subsystems import *

_log = get_logger()

class Agent(AbstractAgent):
    """Agent implementation for FastAPI messagebus."""
    
    class Subsystems(object):
        def __init__(self, *, owner: Agent, core: Core, options: AgentOptions):
            """Initialize subsystems for the agent."""
            self.peerlist = PeerList(core=core)
            self.ping = Ping(core)
            self.rpc = RPC(core=core, owner=owner, peerlist_subsys=self.peerlist)
            self.hello = Hello(core=core)
            self.pubsub = PubSub(core=core,
                                peerlist_subsys=self.peerlist,
                                rpc_subsys=self.rpc,
                                owner=self,
                                tag_vip_id=options.tag_vip_id,
                                tag_refresh_interval=options.tag_refresh_interval)
            self.health = Health(owner=owner, core=core, rpc=self.rpc)
            self.heartbeat = Heartbeat(owner,
                                      core,
                                      rpc=self.rpc,
                                      pubsub=self.pubsub,
                                      heartbeat_autostart=options.heartbeat_autostart,
                                      heartbeat_period=options.heartbeat_period)
            if options.enable_store:
                self.config = ConfigStore(owner, core, self.rpc)
            self.auth = Auth(owner, core, self.rpc)
    
    def __init__(self, _, credentials: Credentials = None, options: AgentOptions = None, 
                address: str = None, **kwargs):
        """
        Initialize the agent.
        
        Args:
            _: Unused parameter (kept for compatibility)
            credentials: Agent credentials
            options: Agent options
            address: Server address
            **kwargs: Additional arguments
        """
        # Set up credentials
        if credentials is None:
            identity = os.environ.get('AGENT_VIP_IDENTITY')
            if not identity:
                identity = kwargs.get('identity')
                if not identity:
                    raise ValueError(f"Environmental variable AGENT_VIP_IDENTITY not set!")
            credentials = Credentials(identity=identity)
            
        # Set up options and context
        if options is None:
            options = AgentOptions()
            
        # Set address from environment if not provided
        if address is None:
            address = os.environ.get('VOLTTRON_SERVER', 'ws://localhost:8000')
            
        context = AgentContext(credentials=credentials, options=options, address=address)
        
        # Build the core
        self.core = Core(owner=self, context=context)
        
        # Set up subsystems
        self.vip = Agent.Subsystems(owner=self, core=self.core, options=options)
        
        # Set up the core
        self.core.setup()
        
        # Export version method
        self.vip.rpc.export(self.core.version, "agent.version")
    
    def start(self):
        """Start the agent."""
        self.core.start()
    
    def stop(self):
        """Stop the agent."""
        self.core.stop()
    
    @staticmethod
    def get_credentials(identity: str) -> Credentials:
        """Create credentials with the given identity."""
        return Credentials(identity=identity)

class BasicAgent(object):
    """Basic agent implementation."""
    
    def __init__(self, **kwargs):
        """Initialize the basic agent."""
        kwargs.pop("identity", None)
        super(BasicAgent, self).__init__(**kwargs)
        self.core = BasicCore(self)

def build_agent(*, address=None, credentials: Credentials):
    """Build an agent with the given address and credentials."""
    raise NotImplementedError()