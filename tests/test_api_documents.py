from urllib.parse import quote

import pytest
from starlette.testclient import TestClient


def test_docs_pagination(client: TestClient, allowed_root, page_pair, alto_pair):
    r = client.get("/api/docs", params={"dir": str(allowed_root), "page": 1, "per_page": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1
    assert body["pages"] == 2


def test_docs_empty_page(client: TestClient, allowed_root, page_pair, alto_pair):
    r = client.get("/api/docs", params={"dir": str(allowed_root), "page": 999, "per_page": 20})
    assert r.status_code == 200
    assert r.json()["items"] == []


def test_overlay(client: TestClient, allowed_root, page_pair):
    r = client.get(
        "/api/overlay/sample_page",
        params={"dir": str(allowed_root)},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["format"] == "PAGE"
    assert data["doc_id"] == "sample_page"


def test_path_traversal(client: TestClient, allowed_root, monkeypatch):
    monkeypatch.setattr("app.config.settings.ALLOWED_ROOT", allowed_root)
    r = client.get("/api/docs", params={"dir": "/etc"})
    assert r.status_code == 403
    assert r.json()["detail"]["error"] == "access_denied"


def test_missing_dir(client: TestClient, allowed_root):
    r = client.get("/api/docs", params={"dir": str(allowed_root / "nope")})
    assert r.status_code == 404


def test_select_dir(client: TestClient, allowed_root, page_pair):
    r = client.post("/api/dirs/select", json={"path": str(allowed_root)})
    assert r.status_code == 200
    b = r.json()
    assert b["valid"] is True
    assert b["doc_count"] >= 1


def test_dirs_pagination(client: TestClient, allowed_root):
    for i in range(5):
        (allowed_root / f"f{i:03d}.txt").write_text("x", encoding="utf-8")
    r = client.get("/api/dirs", params={"path": str(allowed_root), "page": 1, "per_page": 2})
    assert r.status_code == 200
    b = r.json()
    assert b["total"] >= 5
    assert len(b["entries"]) == 2
    assert b["page"] == 1
    assert b["per_page"] == 2
    assert b["pages"] >= 3


def test_image_serves(client: TestClient, allowed_root, page_pair):
    q = quote(str(allowed_root), safe="")
    r = client.get(f"/api/image/sample_page?dir={q}")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("image/")
