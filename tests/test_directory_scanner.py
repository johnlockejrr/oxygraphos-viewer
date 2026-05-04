from pathlib import Path

from PIL import Image

from app.services.directory_scanner import scan_directory, scan_directory_tree


def test_scan_stem_matching(allowed_root: Path):
    Image.new("RGB", (10, 10), color=(1, 2, 3)).save(allowed_root / "a.jpg", "JPEG")
    (allowed_root / "a.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<PcGtsDocument xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">
  <Page imageFilename="a.jpg" imageWidth="10" imageHeight="10">
    <TextRegion id="r1"><Coords points="0,0 10,0 10,10 0,10"/></TextRegion>
  </Page>
</PcGtsDocument>""",
        encoding="utf-8",
    )
    pairs = scan_directory(allowed_root)
    assert len(pairs) == 1
    assert pairs[0][0].stem == "a"
    assert pairs[0][2] == "PAGE"


def test_scan_image_filename(allowed_root: Path):
    Image.new("RGB", (5, 5), color=(1, 2, 3)).save(allowed_root / "img.png", "PNG")
    (allowed_root / "p.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<PcGtsDocument xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">
  <Page imageFilename="img.png" imageWidth="5" imageHeight="5">
    <TextRegion id="r1"><Coords points="0,0 5,0 5,5 0,5"/></TextRegion>
  </Page>
</PcGtsDocument>""",
        encoding="utf-8",
    )
    pairs = scan_directory(allowed_root)
    assert len(pairs) == 1
    assert pairs[0][1].name == "img.png"


def test_scan_empty(allowed_root: Path):
    assert scan_directory(allowed_root) == []


def test_scan_mixed_page_alto(allowed_root: Path, page_pair, alto_pair):
    pairs = scan_directory(allowed_root)
    fmts = {p[2] for p in pairs}
    assert fmts == {"PAGE", "ALTO"}


def test_scan_directory_tree_finds_nested_xml(allowed_root: Path):
    sub = allowed_root / "batch" / "mss-1"
    sub.mkdir(parents=True)
    Image.new("RGB", (4, 4), color=(1, 2, 3)).save(sub / "page-000.jpg", "JPEG")
    (sub / "page-000.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<PcGtsDocument xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">
  <Page imageFilename="page-000.jpg" imageWidth="4" imageHeight="4">
    <TextRegion id="r1"><Coords points="0,0 4,0 4,4 0,4"/></TextRegion>
  </Page>
</PcGtsDocument>""",
        encoding="utf-8",
    )
    assert scan_directory(allowed_root) == []
    pairs = scan_directory_tree(allowed_root)
    assert len(pairs) == 1
    assert pairs[0][0].name == "page-000.xml"
    assert pairs[0][1].name == "page-000.jpg"
