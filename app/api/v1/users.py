from fastapi import APIRouter, Depends, HTTPException

from app.models.users import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter()

# Dependency Injection provider
def get_user_service():
    return UserService()

@router.post("/", response_model=UserResponse)
def create_user(
    user_in: UserCreate, 
    service: UserService = Depends(get_user_service)
):
    try:
        return service.create_user(user_in)
    except ValueError as e:
        # Translate business logic errors into HTTP errors
        raise HTTPException(status_code=400, detail=str(e))