"""Record manager: content hashing and duplicate detection."""
import hashlib

from app.db.supabase import get_supabase_client


def hash_content(content: bytes) -> str:
    """Return SHA-256 hex digest of raw file bytes."""
    return hashlib.sha256(content).hexdigest()


def find_existing_document(user_id: str, filename: str) -> dict | None:
    """Look up an existing document by user + filename. Returns the row or None."""
    supabase = get_supabase_client()
    result = (
        supabase.table("documents")
        .select("*")
        .eq("user_id", user_id)
        .eq("filename", filename)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None
