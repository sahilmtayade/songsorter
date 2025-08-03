"""Health check router for monitoring and status endpoints."""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

import httpx
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.core.config import Settings
from app.core.dependencies import get_current_settings, get_http_client
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    checks: Dict[str, Any]


class ServiceCheck(BaseModel):
    """Individual service check result."""
    status: str
    response_time_ms: int
    message: str


@router.get("/", response_model=HealthResponse, summary="Basic health check")
async def health_check(
    settings: Settings = Depends(get_current_settings)
) -> HealthResponse:
    """
    Basic health check endpoint.
    
    Returns the current status and basic information about the service.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        checks={}
    )


@router.get("/detailed", response_model=HealthResponse, summary="Detailed health check")
async def detailed_health_check(
    settings: Settings = Depends(get_current_settings),
    client: httpx.AsyncClient = Depends(get_http_client),
) -> HealthResponse:
    """
    Detailed health check that tests external dependencies.
    
    This endpoint checks:
    - Spotify API connectivity
    - Basic service functionality
    """
    logger.info("Running detailed health check")
    
    checks = {}
    overall_status = "healthy"
    
    # Test Spotify API connectivity
    spotify_check = await _check_spotify_api(client)
    checks["spotify_api"] = spotify_check
    
    if spotify_check["status"] != "healthy":
        overall_status = "degraded"
    
    # Test basic functionality
    functionality_check = await _check_basic_functionality()
    checks["basic_functionality"] = functionality_check
    
    if functionality_check["status"] != "healthy":
        overall_status = "unhealthy"
    
    logger.info(f"Health check completed with status: {overall_status}")
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc),
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        checks=checks
    )


@router.get("/ready", summary="Readiness probe")
async def readiness_check(
    settings: Settings = Depends(get_current_settings)
) -> Dict[str, str]:
    """
    Kubernetes-style readiness probe.
    
    Returns 200 if the service is ready to handle requests.
    """
    # Add any readiness checks here (database connections, etc.)
    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT
    }


@router.get("/live", summary="Liveness probe")
async def liveness_check() -> Dict[str, str]:
    """
    Kubernetes-style liveness probe.
    
    Returns 200 if the service is alive and should not be restarted.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


async def _check_spotify_api(client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check Spotify API connectivity."""
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Test basic connectivity to Spotify API (public endpoint)
        response = await client.get(
            "https://api.spotify.com/v1/browse/categories",
            timeout=5.0
        )
        
        end_time = asyncio.get_event_loop().time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        if response.status_code == 401:
            # 401 is expected for unauthenticated requests, but shows API is reachable
            return {
                "status": "healthy",
                "response_time_ms": response_time_ms,
                "message": "Spotify API is reachable"
            }
        elif response.status_code == 200:
            return {
                "status": "healthy", 
                "response_time_ms": response_time_ms,
                "message": "Spotify API is fully accessible"
            }
        else:
            return {
                "status": "degraded",
                "response_time_ms": response_time_ms,
                "message": f"Spotify API returned status {response.status_code}"
            }
            
    except asyncio.TimeoutError:
        return {
            "status": "unhealthy",
            "response_time_ms": 5000,
            "message": "Spotify API timeout"
        }
    except Exception as e:
        end_time = asyncio.get_event_loop().time()
        response_time_ms = int((end_time - start_time) * 1000)
        return {
            "status": "unhealthy",
            "response_time_ms": response_time_ms,
            "message": f"Spotify API error: {str(e)}"
        }


async def _check_basic_functionality() -> Dict[str, Any]:
    """Check basic application functionality."""
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Test basic imports and functionality
        from app.services.spotify_service import SpotifyService
        from app.schemas.spotify import Track, Artist
        
        # Test basic object creation
        test_artist = Artist(id="test", name="Test Artist")
        test_track = Track(
            id="test",
            name="Test Track", 
            uri="spotify:track:test",
            artists=[test_artist]
        )
        
        end_time = asyncio.get_event_loop().time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        return {
            "status": "healthy",
            "response_time_ms": response_time_ms,
            "message": "Basic functionality working"
        }
        
    except Exception as e:
        end_time = asyncio.get_event_loop().time()
        response_time_ms = int((end_time - start_time) * 1000)
        return {
            "status": "unhealthy",
            "response_time_ms": response_time_ms,
            "message": f"Basic functionality error: {str(e)}"
        }