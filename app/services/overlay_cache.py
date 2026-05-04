from __future__ import annotations

import threading
from pathlib import Path

from cachetools import LRUCache

from app.config import settings
from app.models.document import OverlayData
from app.services.doc_index import find_pair
from app.services.xml_parser import parse_xml

_cache: LRUCache[tuple[str, str], tuple[float, OverlayData]] = LRUCache(
    maxsize=settings.OVERLAY_CACHE_SIZE
)
_lock = threading.Lock()


def get_overlay(base_dir: Path, doc_id: str) -> OverlayData | None:
    hit = find_pair(base_dir, doc_id)
    if not hit:
        return None
    xml_path, image_path, _fmt = hit
    key = (str(base_dir.resolve()), doc_id)
    mtime = xml_path.stat().st_mtime
    with _lock:
        cached = _cache.get(key)
        if cached is not None and cached[0] == mtime:
            return cached[1]
        data = parse_xml(xml_path, image_path, doc_id)
        _cache[key] = (mtime, data)
        return data


def clear_overlay_cache() -> None:
    with _lock:
        _cache.clear()
