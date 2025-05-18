# src/volttron/types/auth/auth_credentials.py
"""Credentials class for agent authentication."""
import json
import os
from dataclasses import dataclass

@dataclass
class Credentials:
    """Credentials for agent authentication."""
    identity: str
    
    @staticmethod
    def create(*, identity: str) -> 'Credentials':
        """Create credentials with the given identity."""
        return Credentials(identity=identity)
    
    @classmethod
    def from_env(cls) -> 'Credentials':
        """Create credentials from environment variables."""
        cred_str = os.environ.get('AGENT_CREDENTIALS')
        if not cred_str:
            # Try to get identity from other environment variables
            identity = os.environ.get('AGENT_VIP_IDENTITY')
            if not identity:
                raise ValueError("No credentials found in environment")
            return cls(identity=identity)
        
        try:
            data = json.loads(cred_str)
            return cls(identity=data.get('identity', ''))
        except Exception as e:
            raise ValueError(f"Failed to parse credentials: {e}")