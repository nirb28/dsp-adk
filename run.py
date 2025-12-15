"""
Run script for the ADK server.
"""
import uvicorn
from dotenv import load_dotenv

from app.config import get_settings

# Load environment variables
load_dotenv()


def main():
    """Run the ADK server."""
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
