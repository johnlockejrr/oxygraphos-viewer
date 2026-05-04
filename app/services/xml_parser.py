from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Literal

from lxml import etree
from PIL import Image

from app.models.document import BaselineData, OverlayData, Point, RegionData, TextLineData
from app.utils.geometry import bbox_to_polygon, normalize_points
from app.utils.namespace import detect_format, local_name

logger = logging.getLogger(__name__)

# ALTO <Tags> section: tag definitions referenced by TAGREFS (IDs point here).
_ALTO_TAGS_SECTION_TYPES = frozenset(
    {
        "Tag",
        "OtherTag",
        "LayoutTag",
        "StructureTag",
        "ParagraphTag",
        "ContentTag",
    }
)

PAGE_REGION_TYPES = frozenset(
    {
        "TextRegion",
        "ImageRegion",
        "TableRegion",
        "SeparatorRegion",
        "GraphicRegion",
        "ChartRegion",
        "MathsRegion",
        "ChemRegion",
        "MusicRegion",
        "AdvertRegion",
        "NoiseRegion",
        "UnknownRegion",
    }
)


def _page_elements(root: etree._Element) -> list[etree._Element]:
    return root.xpath("//*[local-name()='Page']")


def _strip_type_prefix(custom: str) -> str:
    s = custom.strip()
    m = re.match(r"type:\s*([^;]+)\s*;?", s, re.I)
    if m:
        rest = s[m.end() :].strip().lstrip(";").strip()
        return rest or m.group(1).strip()
    return s


def _page_label(el: etree._Element) -> str | None:
    cid = el.get("id") or ""
    custom = el.get("custom")
    if custom:
        return _strip_type_prefix(custom)
    return cid or None


def _coords_points(el: etree._Element, width: int, height: int) -> list[Point]:
    for child in el:
        if local_name(child) == "Coords":
            pts = child.get("points")
            if pts:
                return normalize_points(pts, width, height)
    return []


def _baseline_from_line(line_el: etree._Element, width: int, height: int) -> BaselineData | None:
    lid = line_el.get("id") or "baseline"
    for child in line_el:
        if local_name(child) == "Baseline":
            raw = child.get("points")
            if not raw:
                return None
            pts = normalize_points(raw, width, height)
            if pts:
                return BaselineData(id=lid, points=pts)
    return None


def _bbox_polygon_from_textlines(textlines: list[TextLineData]) -> list[Point]:
    """Axis-aligned rectangle covering all text line polygons (normalized space)."""
    xs: list[float] = []
    ys: list[float] = []
    for tl in textlines:
        for p in tl.coords:
            xs.append(p.x)
            ys.append(p.y)
    if not xs:
        return []
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return [
        Point(x=min_x, y=min_y),
        Point(x=max_x, y=min_y),
        Point(x=max_x, y=max_y),
        Point(x=min_x, y=max_y),
    ]


def _parse_page_regions(page_el: etree._Element, width: int, height: int) -> list[RegionData]:
    regions: list[RegionData] = []
    for el in page_el:
        ln = local_name(el)
        if ln not in PAGE_REGION_TYPES:
            continue
        rid = el.get("id") or ln
        label = _page_label(el)
        coords = _coords_points(el, width, height)
        textlines: list[TextLineData] = []
        if ln == "TextRegion":
            for child in el:
                if local_name(child) == "TextLine":
                    tid = child.get("id") or "line"
                    tl_label = _page_label(child)
                    tcoords = _coords_points(child, width, height)
                    if not tcoords:
                        continue
                    bl = _baseline_from_line(child, width, height)
                    textlines.append(
                        TextLineData(id=tid, label=tl_label, coords=tcoords, baseline=bl)
                    )
        if not coords:
            if textlines:
                coords = _bbox_polygon_from_textlines(textlines)
            if not coords:
                logger.warning("Skipping %s without valid Coords: %s", ln, rid)
                continue
        regions.append(RegionData(id=rid, type=ln, label=label, coords=coords, textlines=textlines))
    return regions


def _parse_page(root: etree._Element, doc_id: str, image_path: Path) -> OverlayData:
    pages = _page_elements(root)
    if not pages:
        raise ValueError("No Page element in PAGE-XML")
    page_el = pages[0]
    w_raw = page_el.get("imageWidth")
    h_raw = page_el.get("imageHeight")
    width, height = 0, 0
    if w_raw and h_raw:
        try:
            width, height = int(w_raw), int(h_raw)
        except ValueError:
            width, height = 0, 0
    if width <= 0 or height <= 0:
        with Image.open(image_path) as img:
            width, height = img.size
    regions = _parse_page_regions(page_el, width, height)
    return OverlayData(
        doc_id=doc_id,
        image_width=width,
        image_height=height,
        format="PAGE",
        regions=regions,
    )


def _alto_header_tag_id(el: etree._Element) -> str | None:
    return el.get("ID") or el.get("id")


def _alto_header_tag_label(el: etree._Element) -> str:
    return (
        el.get("LABEL")
        or el.get("label")
        or el.get("TYPE")
        or el.get("type")
        or ""
    ).strip()


def _alto_build_tag_map(root: etree._Element) -> dict[str, str]:
    """Map tag @ID → display label from the ALTO <Tags> header (Tag, OtherTag, …)."""
    tags: dict[str, str] = {}
    for tags_el in root.xpath("//*[local-name()='Tags']"):
        for el in tags_el.iter():
            if local_name(el) not in _ALTO_TAGS_SECTION_TYPES:
                continue
            tid = _alto_header_tag_id(el)
            if not tid:
                continue
            lab = _alto_header_tag_label(el)
            if lab:
                tags[tid] = lab
    return tags


def _alto_strings_label(line_el: etree._Element) -> str | None:
    contents: list[str] = []
    for el in line_el.iter():
        if local_name(el) == "String":
            c = el.get("CONTENT")
            if c:
                contents.append(c)
    if not contents:
        return None
    return " ".join(contents)


def _alto_line_label(line_el: etree._Element, tag_map: dict[str, str]) -> str | None:
    refs = line_el.get("TAGREFS") or line_el.get("tagrefs")
    if refs:
        parts = []
        for r in refs.split():
            if r in tag_map and tag_map[r]:
                parts.append(tag_map[r])
        if parts:
            return " ".join(parts)
    sl = _alto_strings_label(line_el)
    if sl:
        return sl
    return line_el.get("ID")


def _alto_block_label(block_el: etree._Element, tag_map: dict[str, str]) -> str | None:
    refs = block_el.get("TAGREFS") or block_el.get("tagrefs")
    if refs:
        parts = []
        for r in refs.split():
            if r in tag_map and tag_map[r]:
                parts.append(tag_map[r])
        if parts:
            return " ".join(parts)
    return block_el.get("ID")


def _alto_baseline_from_attr(
    line_el: etree._Element, page_w: int, page_h: int
) -> BaselineData | None:
    raw = line_el.get("BASELINE")
    if not raw:
        return None
    parts = raw.replace(",", " ").split()
    if len(parts) < 4 or len(parts) % 2 != 0:
        return None
    pts: list[Point] = []
    for i in range(0, len(parts), 2):
        try:
            x = float(parts[i]) / page_w
            y = float(parts[i + 1]) / page_h
        except (ValueError, ZeroDivisionError):
            return None
        pts.append(Point(x=x, y=y))
    if len(pts) < 2:
        return None
    lid = line_el.get("ID") or "baseline"
    return BaselineData(id=lid, points=pts)


def _alto_bbox(el: etree._Element) -> tuple[float, float, float, float] | None:
    try:
        h = float(el.get("HPOS", "nan"))
        v = float(el.get("VPOS", "nan"))
        w = float(el.get("WIDTH", "nan"))
        hgt = float(el.get("HEIGHT", "nan"))
    except (TypeError, ValueError):
        return None
    if w <= 0 or hgt <= 0:
        return None
    return h, v, w, hgt


def _parse_alto(root: etree._Element, doc_id: str, image_path: Path) -> OverlayData:
    tag_map = _alto_build_tag_map(root)
    layout_pages = root.xpath("//*[local-name()='Layout']/*[local-name()='Page']")
    if not layout_pages:
        raise ValueError("No Layout/Page in ALTO-XML")
    page_el = layout_pages[0]
    try:
        p_w = int(float(page_el.get("WIDTH", 0)))
        p_h = int(float(page_el.get("HEIGHT", 0)))
    except (TypeError, ValueError):
        p_w, p_h = 0, 0
    if p_w <= 0 or p_h <= 0:
        with Image.open(image_path) as img:
            p_w, p_h = img.size

    regions: list[RegionData] = []

    for block in page_el.iter():
        if local_name(block) != "TextBlock":
            continue
        bid = block.get("ID") or "block"
        bbox = _alto_bbox(block)
        if not bbox:
            continue
        h, v, w, hgt = bbox
        coords = bbox_to_polygon(h / p_w, v / p_h, w / p_w, hgt / p_h)
        blabel = _alto_block_label(block, tag_map)
        textlines: list[TextLineData] = []
        for line_el in block:
            if local_name(line_el) != "TextLine":
                continue
            lid = line_el.get("ID") or "line"
            lbbox = _alto_bbox(line_el)
            if not lbbox:
                continue
            lh, lv, lw, lhgt = lbbox
            tcoords = bbox_to_polygon(lh / p_w, lv / p_h, lw / p_w, lhgt / p_h)
            tlabel = _alto_line_label(line_el, tag_map)
            bl = _alto_baseline_from_attr(line_el, p_w, p_h)
            textlines.append(TextLineData(id=lid, label=tlabel, coords=tcoords, baseline=bl))
        regions.append(
            RegionData(
                id=bid,
                type="TextBlock",
                label=blabel,
                coords=coords,
                textlines=textlines,
            )
        )

    return OverlayData(
        doc_id=doc_id,
        image_width=p_w,
        image_height=p_h,
        format="ALTO",
        regions=regions,
    )


def parse_xml(xml_path: Path, image_path: Path, doc_id: str) -> OverlayData:
    try:
        tree = etree.parse(str(xml_path))
    except etree.XMLSyntaxError as e:
        raise ValueError(f"XML syntax error: {e}") from e
    root = tree.getroot()
    fmt = detect_format(root)
    if fmt == "PAGE":
        return _parse_page(root, doc_id, image_path)
    if fmt == "ALTO":
        return _parse_alto(root, doc_id, image_path)
    raise ValueError("Unknown XML format")
