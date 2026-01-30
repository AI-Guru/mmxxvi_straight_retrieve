"""FastAPI application entry point for RAG API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from routers import upload_router, documents_router, search_router
from models.schemas import StatusResponse
from store import get_store, close_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup - initialize store
    print("RAG API starting up...")
    await get_store()
    print("LangGraph store initialized")
    yield
    # Shutdown
    print("RAG API shutting down...")
    await close_store()


app = FastAPI(
    title="RAG Document API",
    description="Document upload, storage, and vector search API using LangGraph store",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router)
app.include_router(documents_router)
app.include_router(search_router)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
async def root():
    """Redirect to static frontend."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")


@app.get("/api/status", response_model=StatusResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    return StatusResponse(
        status="healthy",
        version="1.0.0",
        database="connected",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
