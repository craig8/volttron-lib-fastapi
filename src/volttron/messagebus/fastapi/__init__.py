"""
VOLTTRON FastAPI MessageBus implementation package.
"""
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("volttron-lib-fastapi")
except PackageNotFoundError:
    __version__ = "unknown"