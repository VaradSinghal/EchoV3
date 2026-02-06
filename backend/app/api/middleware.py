from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from typing import Dict, Tuple
from collections import defaultdict
import time
import logging

from app.core.security import verify_token

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    JWT token validation middleware.
    Validates Bearer tokens for protected routes.
    """
    
    # Routes that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/auth/signup",
        "/api/auth/login",
        "/api/auth/github",
        "/api/auth/github/callback",
        "/api/auth/refresh",
    }
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        # Skip auth for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Get Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing authentication token"}
            )
        
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authentication scheme"}
            )
        
        token = auth_header.split(" ")[1]
        payload = verify_token(token)
        
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"}
            )
        
        # Add user ID to request state for downstream use
        request.state.user_id = payload.sub
        
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware per IP address and user.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: Dict[str, list] = defaultdict(list)
    
    def _get_client_key(self, request: Request) -> str:
        """Get unique key for rate limiting (IP + user if authenticated)."""
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", None)
        
        if user_id:
            return f"user:{user_id}"
        return f"ip:{client_ip}"
    
    def _clean_old_requests(self, key: str, current_time: float):
        """Remove requests older than 1 minute."""
        cutoff = current_time - 60
        self.request_counts[key] = [
            ts for ts in self.request_counts[key] if ts > cutoff
        ]
    
    async def dispatch(self, request: Request, call_next):
        current_time = time.time()
        client_key = self._get_client_key(request)
        
        # Clean old requests
        self._clean_old_requests(client_key, current_time)
        
        # Check rate limit
        if len(self.request_counts[client_key]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please try again later."}
            )
        
        # Record request
        self.request_counts[client_key].append(current_time)
        
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Request logging middleware.
    Logs all incoming requests with timing information.
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={process_time:.3f}s"
        )
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
