#!/usr/bin/env python3
# scripts/run_server.py
"""
Run the VOLTTRON FastAPI messagebus server in the foreground.
"""
import uvicorn
import argparse
import logging
import sys
import os

def main():
    """Run the FastAPI messagebus server in the foreground."""
    parser = argparse.ArgumentParser(description="Run the VOLTTRON FastAPI messagebus server")
    parser.add_argument("--host", default="0.0.0.0", 
                       help="Host to listen on (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, 
                       help="Port to listen on (default: 8000)")
    parser.add_argument("--log-level", default="info", 
                       help="Log level (default: info)")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger = logging.getLogger(__name__)
    
    # Print startup message
    logger.info("=" * 60)
    logger.info(f"Starting VOLTTRON FastAPI messagebus server")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Log level: {args.log_level}")
    logger.info(f"Press Ctrl+C to stop the server")
    logger.info("=" * 60)
    
    try:
        # Run server (this blocks until the server is stopped)
        uvicorn.run(
            "volttron.messagebus.fastapi.server.app:create_app",
            host=args.host,
            port=args.port,
            log_level=args.log_level,
            factory=True
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Error running server: {e}", exc_info=True)
        return 1
        
    logger.info("Server shutdown complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())