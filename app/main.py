# from fastapi import FastAPI
# from app.api.v1.endpoints.recipes import router as recipes_router

# app = FastAPI(title="RecipeGen API")
# app.include_router(recipes_router)

# @app.get("/health")
# def health():
#     return {"status": "ok"}
# """FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from dotenv import load_dotenv

from app.config import settings
from app.api.v1.api import api_router
from app.database import Base, engine, apply_startup_schema_patches

load_dotenv()

# Create database tables from current schema
Base.metadata.create_all(bind=engine)
apply_startup_schema_patches()

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Smart household food management system API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Food Management API", "version": settings.VERSION, "docs": "/docs"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}


def custom_openapi():
    """Customize OpenAPI schema for cookie-based authentication."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="Smart household food management system API",
        routes=app.routes,
    )

    # Add cookie security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "cookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "access_token",
            "description": "Access token stored in HTTP-only cookie"
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
