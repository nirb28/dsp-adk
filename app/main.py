"""
Main FastAPI application for the Agent Development Kit (ADK).
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings, ensure_directories
from .api import agents_router, tools_router, mcp_servers_router, graphs_router, adapters_router, telemetry_router, repository_router
from .services.auth_service import get_auth_service
from .services.telemetry_service import get_telemetry_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    
    # Startup
    logger.info("Starting Agent Development Kit (ADK)")
    ensure_directories(settings)
    logger.info(f"Storage directories initialized at {settings.storage_path}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ADK")
    auth_service = get_auth_service()
    await auth_service.close()
    telemetry_service = get_telemetry_service()
    await telemetry_service.close()


# Create FastAPI app
app = FastAPI(
    title="Agent Development Kit (ADK)",
    description="""
## Agent Development Kit (ADK)

A comprehensive platform for developing, configuring, and managing AI agents with:

- **Agents**: Configure AI agents with LLM providers, tools, and capabilities
- **Tools**: Define custom tools with OpenAI-compatible schemas
- **MCP Servers**: Integrate Model Context Protocol servers for extended functionality
- **Graphs**: Create LangGraph pipelines and other workflow orchestrations
- **Adapters**: Add cross-cutting concerns like security, observability, caching, rate limiting
- **Telemetry**: OpenTelemetry integration for logging all agent actions

### Authentication

All write operations require JWT authentication from the DSP JWT service.
Include the JWT token in the `Authorization` header: `Bearer <token>`

### Security

- Agents, tools, MCP servers, and graphs can be configured with:
  - `jwt_required`: Whether authentication is required
  - `allowed_groups`: JWT groups that can access the resource
  - `allowed_roles`: JWT roles that can access the resource
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


# Include routers
app.include_router(agents_router)
app.include_router(tools_router)
app.include_router(mcp_servers_router)
app.include_router(graphs_router)
app.include_router(adapters_router)
app.include_router(telemetry_router)
app.include_router(repository_router)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Agent Development Kit (ADK)",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "agents": "/agents",
            "tools": "/tools",
            "mcp_servers": "/mcp-servers",
            "graphs": "/graphs",
            "adapters": "/adapters",
            "telemetry": "/telemetry",
            "repository": "/repository"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "adk"}


@app.get("/config", tags=["Health"])
async def get_config():
    """Get current configuration (non-sensitive)."""
    settings = get_settings()
    return {
        "jwt_service_url": settings.jwt_service_url,
        "storage_path": settings.storage_path,
        "agents_dir": settings.agents_dir,
        "tools_dir": settings.tools_dir,
        "graphs_dir": settings.graphs_dir,
        "mcp_servers_dir": settings.mcp_servers_dir,
        "log_level": settings.log_level
    }
