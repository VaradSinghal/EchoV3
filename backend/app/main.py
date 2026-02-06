from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints.auth import router as auth_router
from app.api.middleware import JWTAuthMiddleware, RateLimitMiddleware, RequestLoggingMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add custom middleware (order matters: last added = first executed)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
app.add_middleware(JWTAuthMiddleware)

# Include routers
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "Welcome to Echov3 API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
