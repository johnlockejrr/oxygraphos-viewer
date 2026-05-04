import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response

from app.config import settings
from app.services.doc_index import find_pair
from app.services.thumbnail_service import get_thumbnail
from app.utils.paths import resolve_under_root

logger = logging.getLogger(__name__)

router = APIRouter(tags=["media"])

_PLACEHOLDER_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" width="150" height="200" viewBox="0 0 150 200">
  <rect width="150" height="200" fill="#0a0a0c"/>
  <text x="75" y="100" fill="#55544f" font-family="monospace" font-size="10" text-anchor="middle">No image</text>
</svg>"""


@router.get("/image/{doc_id}")
async def get_image(
    doc_id: str,
    dir: str = Query(...),
):
    base = resolve_under_root(dir, settings.ALLOWED_ROOT)
    hit = find_pair(base, doc_id)
    if not hit:
        raise HTTPException(status_code=404, detail={"error": "document_not_found"})
    _xml, image_path, _fmt = hit
    path = Path(image_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail={"error": "image_not_found"})
    media = "image/jpeg"
    suf = path.suffix.lower()
    if suf == ".png":
        media = "image/png"
    elif suf in (".tif", ".tiff"):
        media = "image/tiff"
    elif suf == ".webp":
        media = "image/webp"
    return FileResponse(
        path,
        media_type=media,
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/thumb/{doc_id}")
async def get_thumb(
    doc_id: str,
    dir: str = Query(...),
    size: int | None = Query(None, ge=32, le=800),
):
    thumb_size = size if size is not None else settings.THUMB_SIZE
    base = resolve_under_root(dir, settings.ALLOWED_ROOT)
    hit = find_pair(base, doc_id)
    if not hit:
        return Response(
            content=_PLACEHOLDER_SVG,
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=300"},
        )
    _xml, image_path, _fmt = hit
    path = Path(image_path)
    if not path.is_file():
        return Response(
            content=_PLACEHOLDER_SVG,
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=300"},
        )
    try:
        out = await asyncio.to_thread(
            lambda: get_thumbnail(path, thumb_size, settings.THUMB_CACHE_DIR)
        )
    except Exception as e:
        logger.warning("Thumbnail failed for %s: %s", doc_id, e)
        return Response(
            content=_PLACEHOLDER_SVG,
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=60"},
        )
    return FileResponse(
        out,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )
