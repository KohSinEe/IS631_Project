from fastapi import FastAPI
from app.database import Base, engine
from app.routers.account import router as accounts_router


app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

# Register routers
app.include_router(accounts_router)
