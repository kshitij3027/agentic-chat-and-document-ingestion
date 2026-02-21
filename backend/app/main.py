from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback

from app.config import get_settings
from app.routers import auth, threads, chat, documents
from app.routers import settings as settings_router

settings = get_settings()

app = FastAPI(
    title="RAG Masterclass API",
    description="Backend API for the RAG Masterclass application",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return proper JSON response with CORS headers."""
    print(f"Unhandled exception: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Include routers
app.include_router(auth.router)
app.include_router(threads.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(settings_router.router)
