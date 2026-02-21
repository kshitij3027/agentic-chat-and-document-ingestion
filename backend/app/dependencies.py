from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from postgrest.exceptions import APIError
from pydantic import BaseModel

from app.config import get_settings
from app.db.supabase import get_supabase_client

security = HTTPBearer()


class User(BaseModel):
    id: str
    email: str | None = None
    is_admin: bool = False


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Verify Supabase JWT token and extract user info, including admin status."""
    settings = get_settings()
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.supabase_anon_key,
            algorithms=["HS256", "ES256"],
            options={"verify_signature": False},
            audience="authenticated"
        )

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )

        # Query user_profiles for admin status
        is_admin = False
        try:
            supabase = get_supabase_client()
            profile_result = supabase.table("user_profiles").select("is_admin").eq(
                "user_id", user_id
            ).maybe_single().execute()

            if profile_result and profile_result.data:
                is_admin = profile_result.data.get("is_admin", False)
        except APIError:
            pass

        return User(id=user_id, email=email, is_admin=is_admin)

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require the current user to be an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
