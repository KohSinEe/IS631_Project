from fastapi import FastAPI
from app.api.recipes import router as recipes_router

app = FastAPI(title="RecipeGen API")
app.include_router(recipes_router)

@app.get("/health")
def health():
    return {"status": "ok"}
