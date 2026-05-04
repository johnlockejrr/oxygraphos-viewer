from pathlib import Path

from fastapi import HTTPException


def resolve_under_root(path_str: str, allowed_root: Path) -> Path:
    raw = Path(path_str).expanduser()
    try:
        resolved = raw.resolve()
    except OSError as e:
        raise HTTPException(status_code=404, detail={"error": "directory_not_found", "detail": str(e)}) from e
    root = allowed_root.resolve()
    if not resolved.is_relative_to(root):
        raise HTTPException(status_code=403, detail={"error": "access_denied"})
    return resolved
