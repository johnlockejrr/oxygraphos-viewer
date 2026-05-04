from pathlib import Path

import pytest
from PIL import Image
from starlette.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.doc_index import clear_pair_scan_cache
from app.services.overlay_cache import clear_overlay_cache


@pytest.fixture
def allowed_root(tmp_path: Path) -> Path:
    root = tmp_path / "allowed"
    root.mkdir(parents=True)
    return root


@pytest.fixture
def client(allowed_root: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "ALLOWED_ROOT", allowed_root)
    monkeypatch.setattr(settings, "THUMB_CACHE_DIR", allowed_root / "thumbs")
    clear_overlay_cache()
    clear_pair_scan_cache()
    with TestClient(app) as c:
        yield c
    clear_overlay_cache()
    clear_pair_scan_cache()


@pytest.fixture
def page_pair(allowed_root: Path) -> tuple[Path, Path]:
    fixtures = Path(__file__).parent / "fixtures"
    img_path = allowed_root / "sample_page.jpg"
    Image.new("RGB", (100, 200), color=(40, 40, 50)).save(img_path, "JPEG")
    xml_out = allowed_root / "sample_page.xml"
    xml_out.write_text((fixtures / "sample_page.xml").read_text(encoding="utf-8"), encoding="utf-8")
    return xml_out, img_path


@pytest.fixture
def alto_pair(allowed_root: Path) -> tuple[Path, Path]:
    fixtures = Path(__file__).parent / "fixtures"
    img_path = allowed_root / "sample_alto.jpg"
    Image.new("RGB", (1000, 2000), color=(30, 30, 40)).save(img_path, "JPEG")
    xml_out = allowed_root / "sample_alto.xml"
    xml_out.write_text((fixtures / "sample_alto.xml").read_text(encoding="utf-8"), encoding="utf-8")
    return xml_out, img_path
