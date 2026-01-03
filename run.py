"""
Run script for the ADK server.
"""
import logging
import uvicorn
from dotenv import load_dotenv

from app.config import get_settings

# Load environment variables
load_dotenv()


def main():
    """Run the ADK server."""
    settings = get_settings()
    
    # Configure logging for the entire application
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True  # Override any existing configuration
    )
    
    # Set log level for all application loggers
    for logger_name in ['app', 'uvicorn', 'uvicorn.access', 'uvicorn.error']:
        logging.getLogger(logger_name).setLevel(log_level)
    
    print("Starting ADK server...")
    print(f"Host: {settings.host}")
    print(f"Port: {settings.port}")
    print(f"Debug: {settings.debug}")
    print(f"Log Level: {settings.log_level}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
