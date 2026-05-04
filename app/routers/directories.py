import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.models.responses import DirEntry, DirListingResponse, SelectDirBody, SelectDirResponse
from app.services.doc_index import get_pairs_and_nested
from app.utils.paths import resolve_under_root

logger = logging.getLogger(__name__)

router = APIRouter(tags=["directories"])


def _initial_listing_path() -> Path:
    root = settings.ALLOWED_ROOT.resolve()
    start = settings.BROWSE_START_PATH
    if start is None:
        return root
    resolved = start.expanduser().resolve()
    if not resolved.is_relative_to(root):
        logger.warning(
            "BROWSE_START_PATH %s is not under ALLOWED_ROOT %s; using ALLOWED_ROOT",
            resolved,
            root,
        )
        return root
    return resolved


@router.get("/dirs", response_model=DirListingResponse)
async def list_directories(
    path: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int | None = Query(None, ge=1),
) -> DirListingResponse:
    if path is None or path == "":
        path_obj = _initial_listing_path()
    else:
        path_obj = resolve_under_root(path, settings.ALLOWED_ROOT)
    if not path_obj.is_dir():
        raise HTTPException(status_code=404, detail={"error": "directory_not_found"})
    per = per_page if per_page is not None else settings.DIR_BROWSER_PAGE_SIZE
    per = min(per, settings.MAX_DIR_BROWSER_PAGE_SIZE)

    all_entries: list[DirEntry] = []
    try:
        for child in sorted(path_obj.iterdir(), key=lambda p: p.name.lower()):
            try:
                all_entries.append(
                    DirEntry(
                        name=child.name,
                        is_dir=child.is_dir(),
                        path=str(child.resolve()),
                    )
                )
            except OSError as e:
                logger.debug("Skip entry %s: %s", child, e)
    except OSError as e:
        raise HTTPException(status_code=404, detail={"error": "directory_not_found", "detail": str(e)}) from e

    total = len(all_entries)
    pages_count = max(1, (total + per - 1) // per) if total else 1
    start = (page - 1) * per
    slice_entries = all_entries[start : start + per]

    return DirListingResponse(
        path=str(path_obj.resolve()),
        entries=slice_entries,
        total=total,
        page=page,
        per_page=per,
        pages=pages_count,
    )


@router.post("/dirs/select", response_model=SelectDirResponse)
async def select_directory(body: SelectDirBody) -> SelectDirResponse:
    path_obj = resolve_under_root(body.path, settings.ALLOWED_ROOT)
    if not path_obj.is_dir():
        raise HTTPException(status_code=404, detail={"error": "directory_not_found"})
    pairs, _nested = get_pairs_and_nested(path_obj)
    if not pairs:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "no_documents_found",
                "hint": (
                    "No PAGE/ALTO XML paired with an image file was found under this path "
                    "(subfolders are included). Each XML needs a matching image in the same folder "
                    "(same stem or imageFilename / ALTO fileName), or images must exist for pairing."
                ),
            },
        )
    formats = sorted({f for *_, f in pairs})
    return SelectDirResponse(valid=True, doc_count=len(pairs), formats=formats)
