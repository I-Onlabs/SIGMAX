"""
API Versioning Module

This module provides API versioning utilities for SIGMAX FastAPI backend.

Features:
- /api/v1 namespace for all endpoints
- Version detection from headers
- Backward compatibility redirects
- Version deprecation warnings

Usage:
    from versioning import create_versioned_app, v1_router

    # Create versioned FastAPI app
    app = create_versioned_app()

    # Add routes to v1 router
    v1_router.include_router(my_router, prefix="/my-endpoint")
"""

from fastapi import FastAPI, APIRouter, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.routing import APIRoute
from typing import Callable
from loguru import logger


class VersionedRoute(APIRoute):
    """Custom route class for version-aware endpoints"""

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            # Check API version from header
            api_version = request.headers.get("X-API-Version", "v1")

            # Log version usage
            if api_version != "v1":
                logger.warning(f"Unsupported API version requested: {api_version}")

            # Call original handler
            response = await original_route_handler(request)

            # Add version header to response
            response.headers["X-API-Version"] = "v1"
            response.headers["X-API-Supported-Versions"] = "v1"

            return response

        return custom_route_handler


# API Version 1 Router
v1_router = APIRouter(
    prefix="/api/v1",
    route_class=VersionedRoute,
    responses={
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        401: {"description": "Unauthorized - Invalid or missing API key"},
        500: {"description": "Internal Server Error"},
    }
)


def create_versioned_app(
    title: str = "SIGMAX API",
    description: str = "Autonomous Multi-Agent AI Trading OS API",
    version: str = "1.0.0",
    **kwargs
) -> FastAPI:
    """
    Create FastAPI app with versioning support

    Args:
        title: API title
        description: API description
        version: API version
        **kwargs: Additional FastAPI arguments

    Returns:
        FastAPI application instance
    """

    app = FastAPI(
        title=title,
        description=description,
        version=version,
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
        **kwargs
    )

    # Include v1 router
    app.include_router(v1_router)

    return app


def add_legacy_redirects(app: FastAPI):
    """
    Add backward compatibility redirects for legacy endpoints

    Redirects non-versioned endpoints to /api/v1

    Usage:
        add_legacy_redirects(app)
    """

    @app.get("/health", include_in_schema=False)
    async def legacy_health():
        """Redirect to versioned health endpoint"""
        return RedirectResponse(url="/api/v1/health", status_code=301)

    @app.get("/status", include_in_schema=False)
    async def legacy_status():
        """Redirect to versioned status endpoint"""
        return RedirectResponse(url="/api/v1/status", status_code=301)

    @app.get("/metrics", include_in_schema=False)
    async def legacy_metrics():
        """Redirect to versioned metrics endpoint"""
        return RedirectResponse(url="/api/v1/metrics", status_code=301)

    logger.info("✓ Legacy endpoint redirects added")


def add_version_info_endpoint(app: FastAPI):
    """
    Add /api/versions endpoint showing supported API versions

    Usage:
        add_version_info_endpoint(app)
    """

    @app.get("/api/versions", tags=["System"])
    async def api_versions():
        """Get supported API versions"""
        return {
            "supported_versions": ["v1"],
            "default_version": "v1",
            "latest_version": "v1",
            "deprecated_versions": [],
            "endpoints": {
                "v1": {
                    "base_url": "/api/v1",
                    "docs": "/api/v1/docs",
                    "openapi": "/api/v1/openapi.json",
                    "status": "stable"
                }
            }
        }

    logger.info("✓ Version info endpoint added at /api/versions")


# Utility function to extract version from request
def get_api_version(request: Request) -> str:
    """
    Extract API version from request

    Checks in order:
    1. Path prefix (/api/v1/...)
    2. X-API-Version header
    3. Query parameter (?version=v1)
    4. Default to v1

    Args:
        request: FastAPI request object

    Returns:
        API version string (e.g., "v1")
    """

    # Check path
    path = request.url.path
    if path.startswith("/api/v"):
        version_part = path.split("/")[2]  # /api/v1/...
        if version_part.startswith("v"):
            return version_part

    # Check header
    if "X-API-Version" in request.headers:
        return request.headers["X-API-Version"]

    # Check query param
    if "version" in request.query_params:
        return request.query_params["version"]

    # Default
    return "v1"


# Decorator for version-specific endpoints
def requires_version(min_version: str = "v1", max_version: str = "v1"):
    """
    Decorator to enforce API version requirements

    Usage:
        @requires_version(min_version="v1", max_version="v1")
        @app.get("/api/v1/endpoint")
        async def my_endpoint():
            return {"status": "ok"}
    """

    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            version = get_api_version(request)

            # Simple version comparison (assumes v1, v2, v3 format)
            version_num = int(version.replace("v", ""))
            min_num = int(min_version.replace("v", ""))
            max_num = int(max_version.replace("v", ""))

            if not (min_num <= version_num <= max_num):
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Unsupported API version",
                        "message": f"This endpoint requires API version {min_version} to {max_version}",
                        "requested_version": version,
                        "supported_versions": [f"v{i}" for i in range(min_num, max_num + 1)]
                    }
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


if __name__ == "__main__":
    # Self-test
    print("🔢 API Versioning Module Self-Test\n")

    app = create_versioned_app()
    add_legacy_redirects(app)
    add_version_info_endpoint(app)

    print("✓ Versioned app created")
    print("  Docs: /api/v1/docs")
    print("  OpenAPI: /api/v1/openapi.json")
    print("  Version info: /api/versions")
    print("\n✅ Self-test complete!")
