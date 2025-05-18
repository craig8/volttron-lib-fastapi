# src/volttron/types/agent_context.py
"""Agent context and options classes."""
from dataclasses import dataclass
from typing import Optional

from volttron.types.auth.auth_credentials import Credentials

@dataclass
class AgentOptions:
    """Options for agent configuration."""
    heartbeat_autostart: bool = True
    heartbeat_period: int = 60
    enable_store: bool = True
    enable_web: bool = False
    enable_channel: bool = False
    message_bus: str = "fastapi"
    tag_vip_id: Optional[str] = None
    tag_refresh_interval: int = 300

@dataclass
class AgentContext:
    """Context for agent execution."""
    credentials: Credentials
    options: AgentOptions
    address: Optional[str] = None