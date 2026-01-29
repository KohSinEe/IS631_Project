from fastapi import APIRouter, HTTPException
from app.models.user import UserCreate, UserRead
from app.services.users import create_user, get_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead)
def create(user: UserCreate):
    return create_user(user)


@router.get("/{user_id}", response_model=UserRead)
def read(user_id: int):
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404)

    return user
