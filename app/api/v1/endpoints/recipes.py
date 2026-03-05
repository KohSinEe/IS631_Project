import os
from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import DatabaseDep, CurrentUserDep
from app.schemas.recipes import RecipeGenerateRequest, RecipeGenerateResponse
from app.models.user import User
from app.models.user_allergen import UserAllergen
from app.services.recipe_gen import generate_recipes

router = APIRouter()


@router.post("", response_model=RecipeGenerateResponse)
async def generate(req: RecipeGenerateRequest, current_user: CurrentUserDep, db: DatabaseDep):
    # Fetch allergens
    allergens = []
    if req.use_household_allergens and current_user.household_id:
        members = db.query(User).filter(User.household_id == current_user.household_id).all()
        allergens = list({a.allergen for member in members for a in member.allergens})
    else:
        my_allergens = db.query(UserAllergen).filter(UserAllergen.user_id == current_user.id).all()
        allergens = [a.allergen for a in my_allergens]

    # Recipe generation, including allergens

    print("Allergens being passed:", allergens)

    try:
        result = await generate_recipes(
            pantry_items=[i.model_dump() for i in req.items],
            model=os.getenv("OLLAMA_MODEL", "mistral-large-3:675b-cloud"),
            ollama_host=os.getenv("OLLAMA_HOST", "http://ollama:11434"),
            inventory_only=req.inventory_only,
            max_recipes=req.max_recipes,
            preferences=req.preferences,
            use_chat_endpoint=False,
            allergens=allergens,
        )
        return result
    except ValueError as e:
        msg = str(e)
        if "No pantry items" in msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=msg,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg,
        )
