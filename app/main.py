from fastapi import FastAPI
from app.routers import users

app = FastAPI(
    title="Test App",
    description="Fridge Inventory Management Extraordinaire",
    version="0.1.0",
)

app.include_router(users.router)
