from .loop import CoreLoop
from .gevent_loop import GeventCoreLoop

# Export both classes directly
__all__ = ['CoreLoop', 'GeventCoreLoop']