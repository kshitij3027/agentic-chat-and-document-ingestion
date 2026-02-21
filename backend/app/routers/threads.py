from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime

from app.dependencies import get_current_user, User
from app.db.supabase import get_supabase_client
from app.models.schemas import ThreadCreate, ThreadResponse, ThreadUpdate

router = APIRouter(prefix="/threads", tags=["threads"])


@router.get("", response_model=list[ThreadResponse])
async def list_threads(current_user: User = Depends(get_current_user)):
    """List all threads for the current user."""
    supabase = get_supabase_client()
    result = supabase.table("threads").select("*").eq("user_id", current_user.id).order("updated_at", desc=True).execute()
    return result.data


@router.post("", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    thread_data: ThreadCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new thread."""
    supabase = get_supabase_client()

    # Store in database (no more OpenAI thread needed with Responses API)
    now = datetime.utcnow().isoformat()
    result = supabase.table("threads").insert({
        "user_id": current_user.id,
        "title": thread_data.title or "New Chat",
        "created_at": now,
        "updated_at": now,
    }).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create thread"
        )

    return result.data[0]


@router.get("/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific thread."""
    supabase = get_supabase_client()
    result = supabase.table("threads").select("*").eq("id", thread_id).eq("user_id", current_user.id).single().execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    return result.data


@router.patch("/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: str,
    thread_data: ThreadUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a thread's title."""
    supabase = get_supabase_client()

    # First verify the thread belongs to the user
    existing = supabase.table("threads").select("id").eq("id", thread_id).eq("user_id", current_user.id).single().execute()
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    result = supabase.table("threads").update({
        "title": thread_data.title,
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", thread_id).execute()

    return result.data[0]


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a thread."""
    supabase = get_supabase_client()

    # Verify the thread belongs to the user
    result = supabase.table("threads").select("id").eq("id", thread_id).eq("user_id", current_user.id).single().execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Delete from database (messages will cascade delete)
    supabase.table("threads").delete().eq("id", thread_id).execute()
