import hashlib
from pathlib import Path

from PIL import Image


def get_thumbnail(image_path: Path, size: int, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    mtime = int(image_path.stat().st_mtime)
    key = hashlib.md5(f"{image_path}{mtime}{size}".encode()).hexdigest()
    cache_path = cache_dir / f"{key}.jpg"
    if cache_path.exists():
        return cache_path
    with Image.open(image_path) as img:
        img.thumbnail((size, size * 2), Image.Resampling.LANCZOS)
        rgb = img.convert("RGB")
        rgb.save(cache_path, "JPEG", quality=85, optimize=True)
    return cache_path
