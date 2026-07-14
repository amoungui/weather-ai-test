import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import APP_NAME

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for the logging requests
    """

    async def dispatch(self, request: Request, call_next):
        # Start the timer
        start_time = time.time()

        # Log the incoming request
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        # Process the request
        response = await call_next(request)

        # Calculate the processing time
        process_time = time.time() - start_time

        # Log the response
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )

        # Add the processing time header
        response.headers["X-Process-Time"] = str(process_time)

        return response
