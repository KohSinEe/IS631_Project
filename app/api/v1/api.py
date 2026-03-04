"""API v1 router aggregator."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, items, barcode, recipes, usage

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(items.router, prefix="/items", tags=["Items"])
api_router.include_router(barcode.router, prefix="/barcode", tags=["Barcode Scanning"])
api_router.include_router(recipes.router, prefix="/recipes", tags=["Recipes"])
api_router.include_router(usage.router, prefix="/usage", tags=["Usage"])
