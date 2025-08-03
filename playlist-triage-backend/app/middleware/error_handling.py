"""Middleware for error handling and request processing."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException
from app.core.logging import get_logger

logger = get_logger(__name__)


async def error_handling_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware to handle application errors and provide consistent error responses."""
    
    # Generate request ID for tracing
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Log successful requests
        duration = time.time() - start_time
        logger.info(
            f"Request completed - {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Duration: {duration:.3f}s - "
            f"Request ID: {request_id}"
        )
        
        return response
        
    except AppException as e:
        # Handle known application exceptions
        duration = time.time() - start_time
        logger.warning(
            f"Application error - {request.method} {request.url.path} - "
            f"Error: {e.message} - Duration: {duration:.3f}s - "
            f"Request ID: {request_id}",
            extra={"details": e.details}
        )
        
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": {
                    "message": e.message,
                    "details": e.details,
                    "request_id": request_id,
                    "type": type(e).__name__
                }
            }
        )
        
    except Exception as e:
        # Handle unexpected exceptions
        duration = time.time() - start_time
        logger.error(
            f"Unexpected error - {request.method} {request.url.path} - "
            f"Error: {str(e)} - Duration: {duration:.3f}s - "
            f"Request ID: {request_id}",
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "message": "An unexpected error occurred",
                    "request_id": request_id,
                    "type": "InternalServerError"
                }
            }
        )