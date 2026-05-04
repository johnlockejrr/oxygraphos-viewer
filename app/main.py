import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import directories, documents, media, overlays

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.THUMB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Oxygraphos Viewer", lifespan=lifespan)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(directories.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(overlays.router, prefix="/api")
app.include_router(media.router, prefix="/api")

if settings.FRONTEND_DIST and settings.FRONTEND_DIST.is_dir():
    dist = settings.FRONTEND_DIST.resolve()
    assets_dir = dist / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Not Found")
        index = dist / "index.html"
        if not index.is_file():
            from fastapi import HTTPException

            raise HTTPException(status_code=503, detail="Frontend not built")
        candidate = dist / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)
