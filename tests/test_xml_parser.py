from pathlib import Path

from PIL import Image

from app.services.xml_parser import parse_xml


def test_parse_page_fixture(page_pair: tuple[Path, Path]):
    xml_path, image_path = page_pair
    data = parse_xml(xml_path, image_path, "sample_page")
    assert data.format == "PAGE"
    assert data.image_width == 100
    assert data.image_height == 200
    assert len(data.regions) == 2
    text_regions = [r for r in data.regions if r.type == "TextRegion"]
    assert len(text_regions) == 1
    tr = text_regions[0]
    assert tr.id == "r1"
    assert tr.label and "Main title" in tr.label
    assert len(tr.textlines) == 1
    tl = tr.textlines[0]
    assert tl.baseline is not None
    assert len(tl.baseline.points) == 2
    # normalized: (5/100, 40/200) approx
    assert abs(tl.baseline.points[0].x - 0.05) < 0.001
    assert abs(tl.baseline.points[0].y - 0.2) < 0.001


def test_parse_alto_fixture(alto_pair: tuple[Path, Path]):
    xml_path, image_path = alto_pair
    data = parse_xml(xml_path, image_path, "sample_alto")
    assert data.format == "ALTO"
    assert data.image_width == 1000
    assert data.image_height == 2000
    assert len(data.regions) == 1
    b = data.regions[0]
    assert b.type == "TextBlock"
    assert len(b.textlines) == 1
    assert b.textlines[0].label == "hello"
    assert b.textlines[0].baseline is not None
    assert len(b.textlines[0].baseline.points) == 2


def test_parse_alto_other_tag_header_resolves_tagrefs(allowed_root: Path):
    fixtures = Path(__file__).parent / "fixtures"
    img_path = allowed_root / "sample_alto_ot.jpg"
    Image.new("RGB", (1000, 2000), color=(20, 20, 30)).save(img_path, "JPEG")
    xml_path = allowed_root / "sample_alto_other_tag.xml"
    xml_path.write_text((fixtures / "sample_alto_other_tag.xml").read_text(encoding="utf-8"), encoding="utf-8")
    data = parse_xml(xml_path, img_path, "alto_ot")
    assert data.format == "ALTO"
    b = data.regions[0]
    assert b.label == "MainZone"
    assert b.textlines[0].label == "DefaultLine"


def test_page_textregion_without_region_coords_keeps_textlines(allowed_root: Path):
    """eScriptorium dummy TextRegions often omit <Coords> but contain TextLines."""
    img_path = allowed_root / "dummy.jpg"
    Image.new("RGB", (100, 100), color=(1, 1, 1)).save(img_path, "JPEG")
    xml_path = allowed_root / "dummy.xml"
    xml_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">
  <Page imageWidth="100" imageHeight="100">
    <TextRegion id="eSc_dummyblock_">
      <TextLine id="line1">
        <Coords points="10,10 30,10 30,25 10,25"/>
        <Baseline points="10,20 30,20"/>
      </TextLine>
    </TextRegion>
  </Page>
</PcGts>
""",
        encoding="utf-8",
    )
    data = parse_xml(xml_path, img_path, "dummy")
    assert data.format == "PAGE"
    assert len(data.regions) == 1
    r = data.regions[0]
    assert r.type == "TextRegion"
    assert len(r.textlines) == 1
    assert r.textlines[0].baseline is not None
    assert len(r.coords) == 4
    assert abs(r.coords[0].x - 0.1) < 0.001 and abs(r.coords[0].y - 0.1) < 0.001


def test_malformed_xml_no_crash(allowed_root: Path, tmp_path: Path):
    bad = allowed_root / "bad.xml"
    bad.write_text("not xml <<", encoding="utf-8")
    img = allowed_root / "bad.jpg"
    img.write_bytes(b"")
    try:
        parse_xml(bad, img, "bad")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
