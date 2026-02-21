"""Document upload, list, and delete endpoints."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status

from app.dependencies import get_current_user, User
from app.db.supabase import get_supabase_client
from app.services.ingestion_service import process_document

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_TYPES = {
    "text/plain": ".txt",
    "text/markdown": ".md",
    "application/octet-stream": None,  # fallback, check extension
}
ALLOWED_EXTENSIONS = {".txt", ".md"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a document for ingestion."""
    # Validate file extension
    filename = file.filename or "unknown"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10 MB."
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty."
        )

    # Determine content type
    content_type = file.content_type or "text/plain"
    if ext == ".md":
        content_type = "text/markdown"
    elif ext == ".txt":
        content_type = "text/plain"

    supabase = get_supabase_client()

    # Upload to Supabase Storage
    file_id = str(uuid.uuid4())
    storage_path = f"{current_user.id}/{file_id}{ext}"

    supabase.storage.from_("documents").upload(
        path=storage_path,
        file=content,
        file_options={"content-type": content_type},
    )

    # Create document record
    doc_record = {
        "user_id": current_user.id,
        "filename": filename,
        "file_type": content_type,
        "file_size": len(content),
        "storage_path": storage_path,
        "status": "pending",
    }

    result = supabase.table("documents").insert(doc_record).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create document record"
        )

    document = result.data[0]

    # Trigger background processing
    background_tasks.add_task(process_document, document["id"], current_user.id)

    return document


@router.get("")
async def list_documents(current_user: User = Depends(get_current_user)):
    """List all documents for the current user."""
    supabase = get_supabase_client()
    result = supabase.table("documents").select("*").eq(
        "user_id", current_user.id
    ).order("created_at", desc=True).execute()

    return result.data


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a document and its storage file (chunks cascade via FK)."""
    supabase = get_supabase_client()

    # Get document (RLS ensures user owns it)
    result = supabase.table("documents").select("*").eq(
        "id", document_id
    ).eq("user_id", current_user.id).single().execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    doc = result.data

    # Delete from storage
    try:
        supabase.storage.from_("documents").remove([doc["storage_path"]])
    except Exception:
        pass  # Storage file may already be gone

    # Delete document record (chunks cascade)
    supabase.table("documents").delete().eq("id", document_id).execute()

    return {"status": "deleted"}
