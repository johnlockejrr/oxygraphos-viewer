from pathlib import Path

from PIL import Image


def get_image_dimensions(image_path: Path) -> tuple[int, int]:
    with Image.open(image_path) as img:
        return img.size
