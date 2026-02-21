from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)) -> dict:
    """Get the current authenticated user's info."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
    }
