import logging
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.models.document import Document
from app.services.doc_index import display_filename, doc_id_for_xml, get_pairs_and_nested
from app.utils.paths import resolve_under_root

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])


@router.get("/docs")
async def list_documents(
    dir: str = Query(..., description="Absolute directory path"),
    page: int = Query(1, ge=1),
    per_page: int | None = Query(None, ge=1),
) -> dict:
    base = resolve_under_root(dir, settings.ALLOWED_ROOT)
    if not base.is_dir():
        raise HTTPException(status_code=404, detail={"error": "directory_not_found"})

    per = per_page if per_page is not None else settings.PAGE_SIZE
    per = min(per, settings.MAX_PAGE_SIZE)

    pairs, nested = get_pairs_and_nested(base)
    total = len(pairs)
    pages_count = max(1, (total + per - 1) // per) if total else 1
    start = (page - 1) * per
    slice_pairs = pairs[start : start + per]

    dir_q = quote(str(base.resolve()), safe="")
    items: list[Document] = []
    for xml_path, image_path, fmt in slice_pairs:
        doc_id = doc_id_for_xml(base, xml_path, nested)
        items.append(
            Document(
                id=doc_id,
                filename=display_filename(base, xml_path),
                xml_path=str(xml_path),
                image_path=str(image_path),
                format=fmt,  # type: ignore[arg-type]
                thumb_url=f"/api/thumb/{doc_id}?dir={dir_q}",
                image_url=f"/api/image/{doc_id}?dir={dir_q}",
            )
        )

    return {
        "total": total,
        "page": page,
        "per_page": per,
        "pages": pages_count,
        "items": [m.model_dump() for m in items],
    }
