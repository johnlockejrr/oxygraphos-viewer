import logging

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.services.overlay_cache import get_overlay
from app.utils.paths import resolve_under_root

logger = logging.getLogger(__name__)

router = APIRouter(tags=["overlays"])


@router.get("/overlay/{doc_id}")
async def get_document_overlay(
    doc_id: str,
    dir: str = Query(..., description="Absolute directory path"),
) -> dict:
    base = resolve_under_root(dir, settings.ALLOWED_ROOT)
    if not base.is_dir():
        raise HTTPException(status_code=404, detail={"error": "directory_not_found"})
    try:
        data = get_overlay(base, doc_id)
    except ValueError as e:
        logger.warning("Overlay parse error for %s: %s", doc_id, e)
        raise HTTPException(
            status_code=422,
            detail={"error": "xml_parse_error", "detail": str(e)},
        ) from e
    if data is None:
        raise HTTPException(status_code=404, detail={"error": "document_not_found"})
    return data.model_dump()
