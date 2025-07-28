from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging
import os

# Import routers
from .api import webhooks, admin, billing, users
from .database.database import init_db, close_db, db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('saas.log') if os.getenv('ENVIRONMENT') == 'production' else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting FlowLogic RouteAI SaaS Backend...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Test database connection
        db_healthy = await db_manager.health_check()
        if not db_healthy:
            logger.error("Database health check failed!")
        else:
            logger.info("Database health check passed")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down FlowLogic RouteAI SaaS Backend...")
        await close_db()
        logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="FlowLogic RouteAI SaaS Backend",
    description="SaaS backend for FlowLogic RouteAI with authentication, billing, and usage management",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development
        "http://localhost:8080",  # Alternative development port
        "https://app.flowlogic.ai",  # Production frontend
        "https://flowlogic.ai",  # Landing page
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Trusted host middleware for production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["api.flowlogic.ai", "localhost"]
    )


# Custom middleware for request logging and rate limit headers
@app.middleware("http")
async def logging_and_headers_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"{request.method} {request.url.path} - {request.client.host}")
    
    response = await call_next(request)
    
    # Add processing time header
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Add rate limit headers if available
    if hasattr(request.state, 'rate_limit_info'):
        rate_info = request.state.rate_limit_info
        response.headers["X-RateLimit-Limit"] = str(rate_info.get("limit", 0))
        response.headers["X-RateLimit-Remaining"] = str(rate_info.get("remaining", 0))
        response.headers["X-RateLimit-Reset"] = str(int(rate_info.get("reset_time", time.time())))
    
    # Add usage headers if available
    if hasattr(request.state, 'usage_info'):
        usage_info = request.state.usage_info
        response.headers["X-Usage-Limit"] = str(usage_info.get("monthly_limit", 0))
        response.headers["X-Usage-Current"] = str(usage_info.get("current_usage", 0))
        response.headers["X-Usage-Remaining"] = str(usage_info.get("remaining", 0))
    
    # Log response
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, 'request_id', 'unknown')
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "FlowLogic RouteAI SaaS Backend",
        "version": "1.0.0",
        "status": "operational",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "endpoints": {
            "health": "/health",
            "webhooks": "/webhooks",
            "admin": "/admin",
            "billing": "/billing",
            "users": "/users",
            "docs": "/docs" if os.getenv("ENVIRONMENT") != "production" else None
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    try:
        # Check database
        db_healthy = await db_manager.health_check()
        
        # Check database stats
        db_stats = await db_manager.get_stats()
        
        health_status = {
            "status": "healthy" if db_healthy else "unhealthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "checks": {
                "database": "healthy" if db_healthy else "unhealthy",
                "redis": "unknown",  # Would check Redis connection
                "stripe": "unknown",  # Would check Stripe API
            },
            "database_stats": db_stats
        }
        
        status_code = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return JSONResponse(content=health_status, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": "Health check failed"
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


# API version endpoint
@app.get("/version")
async def get_version():
    """Get API version information"""
    return {
        "version": "1.0.0",
        "build_date": "2024-01-01",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "python_version": "3.11+",
        "features": [
            "Firebase Authentication",
            "Stripe Billing",
            "API Key Management",
            "Usage Tracking",
            "Rate Limiting",
            "Admin Dashboard",
            "Webhook Processing"
        ]
    }


# Include routers
app.include_router(webhooks.router)
app.include_router(admin.router)
app.include_router(billing.router)
app.include_router(users.router)


# Development-only endpoints
if os.getenv("ENVIRONMENT") != "production":
    @app.get("/dev/test-auth")
    async def test_auth():
        """Test endpoint for development authentication"""
        return {
            "message": "Use these tokens for testing:",
            "firebase_tokens": {
                "dev_user": "dev_user_1",
                "admin_user": "admin_user"
            },
            "api_keys": {
                "test_key": "fl_test_abcdefghijklmnopqrstuvwxyz123456"
            }
        }
    
    @app.get("/dev/create-test-user")
    async def create_test_user():
        """Create test user for development"""
        # This would create a test user in the database
        return {"message": "Test user creation not implemented yet"}


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT") != "production",
        log_level="info"
    )