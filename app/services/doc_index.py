from __future__ import annotations

import base64
from pathlib import Path

from cachetools import TTLCache

from app.services.directory_scanner import scan_directory_tree

_SCAN_TTL: TTLCache[str, tuple[list[tuple[Path, Path, str]], bool]] = TTLCache(maxsize=128, ttl=45.0)


def _cache_key(base: Path) -> str:
    return str(base.resolve())


def get_pairs_and_nested(base: Path) -> tuple[list[tuple[Path, Path, str]], bool]:
    """Return (pairs, nested_doc_ids) with short-lived cache per root directory."""
    k = _cache_key(base)
    hit = _SCAN_TTL.get(k)
    if hit is not None:
        return hit
    pairs = scan_directory_tree(base)
    base_r = base.resolve()
    nested = any(xml.resolve().parent != base_r for xml, _, _ in pairs)
    val = (pairs, nested)
    _SCAN_TTL[k] = val
    return val


def clear_pair_scan_cache() -> None:
    _SCAN_TTL.clear()


def doc_id_for_xml(base: Path, xml_path: Path, nested: bool) -> str:
    if not nested:
        return xml_path.stem
    rel = xml_path.resolve().relative_to(base.resolve())
    raw = base64.urlsafe_b64encode(rel.as_posix().encode()).decode("ascii")
    return raw.rstrip("=")


def display_filename(base: Path, xml_path: Path) -> str:
    try:
        return str(xml_path.resolve().relative_to(base.resolve()).with_suffix(""))
    except ValueError:
        return xml_path.stem


def find_pair(base_dir: Path, doc_id: str) -> tuple[Path, Path, str] | None:
    pairs, nested = get_pairs_and_nested(base_dir)
    for xml_path, image_path, fmt in pairs:
        if doc_id_for_xml(base_dir, xml_path, nested) == doc_id:
            return xml_path, image_path, fmt
    return None
