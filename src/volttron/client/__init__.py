"""
VIP message class.
Adapted from volttron-core for use with FastAPI messagebus.
"""
import base64
import json
import os
import random
import re
import sys
import uuid

__all__ = ['Message']

# Optimized versions of functions for generating encoded frames will
# be used when available.
_use_json_module = True


class Message(object):
    """VIP message class used for compatibility with VOLTTRON protocol."""

    def __init__(self, peer='', subsystem='', args=None, msg_id='', user='', via=None):
        self.peer = peer
        self.subsystem = subsystem
        self.args = args or []
        self.id = msg_id or str(uuid.uuid4())
        self.user = user
        self.via = via

    @classmethod
    def from_dict(cls, dct):
        """Create a message object from a dictionary."""
        return cls(peer=dct['peer'], subsystem=dct['subsystem'],
                   args=dct['args'], msg_id=dct['id'],
                   user=dct.get('user', ''),
                   via=dct.get('via', None))

    def to_dict(self):
        """Convert to a dictionary."""
        dct = {
            'peer': self.peer,
            'subsystem': self.subsystem,
            'args': self.args,
            'id': self.id,
        }
        if self.user:
            dct['user'] = self.user
        if self.via is not None:
            dct['via'] = self.via
        return dct
        
    @classmethod
    def from_json(cls, json_string):
        """Create a message object from a JSON string."""
        return cls.from_dict(json.loads(json_string))
        
    def to_json(self):
        """Convert to a JSON string."""
        return json.dumps(self.to_dict())

    def __repr__(self):
        attrs = ['peer', 'subsystem', 'args', 'id', 'user', 'via']
        kwargs = ', '.join('%s=%r' % (name, getattr(self, name))
                           for name in attrs)
        return '%s(%s)' % (self.__class__.__name__, kwargs)

    def __str__(self):
        return '<%s at %s>' % (self.__class__.__name__, id(self))