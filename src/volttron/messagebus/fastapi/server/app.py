"""
FastAPI application for VOLTTRON messagebus.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from ..websocket.connection import router as websocket_router

_log = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown events.
    
    This context manager runs before the application starts accepting requests
    and after it finishes processing requests.
    """
    # Startup logic
    _log.info("VOLTTRON FastAPI MessageBus starting up")
    yield
    # Shutdown logic
    _log.info("VOLTTRON FastAPI MessageBus shutting down")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="VOLTTRON FastAPI MessageBus",
        description="WebSocket-based implementation of VOLTTRON messagebus",
        version="0.1.0",
        lifespan=lifespan
    )
    
    # Register WebSocket router
    app.include_router(websocket_router)
    
    @app.get("/")
    async def root():
        """Basic health check endpoint."""
        return {"status": "online", "service": "volttron-messagebus"}
    
    return app