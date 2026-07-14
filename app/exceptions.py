from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AppException(HTTPException):
    """
    Exception personnalized for the application
    """
    def __init__(self, status_code: int, detail: str, error_code: str = None):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        super().__init__(status_code=status_code, detail=detail)

class APIError(Exception):
    """
    Error from external API
    """
    def __init__(self, service: str, message: str, status_code: int = None):
        self.service = service
        self.message = message
        self.status_code = status_code
        super().__init__(f"{service}: {message}")

async def app_exception_handler(request: Request, exc: AppException):
    """
    Manager for the customized exceptions
    """
    logger.error(f"AppException: {exc.detail} (code: {exc.error_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_code": exc.error_code,
            "path": request.url.path,
            "timestamp": datetime.now().isoformat()
        }
    )

async def api_error_handler(request: Request, exc: APIError):
    """
    Manager OF the API error
    """
    logger.error(f"API Error - {exc.service}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code or 503,
        content={
            "error": f"Erreur du service {exc.service}",
            "detail": exc.message,
            "service": exc.service,
            "path": request.url.path,
            "timestamp": datetime.now().isoformat()
        }
    )