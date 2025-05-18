# src/volttron/client/vip/agent/decorators.py
"""Decorators for VIP agents."""
import functools
import inspect
import logging
from typing import Any, Callable

_log = logging.getLogger(__name__)

def annotate(**annotations):
    """Annotate a method with keyworded annotations."""
    def decorator(func):
        for key, value in annotations.items():
            setattr(func, key, value)
        return func
    return decorator

def is_annotated(func, annotation):
    """Check if a function has an annotation."""
    return getattr(func, annotation, None) is not None