"""Generate a tiny JPEG for tests/fixtures (optional)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures" / "sample_image.jpg"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (100, 200), (20, 22, 28)).save(OUT, "JPEG", quality=85)
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
