from __future__ import annotations

from typing import Literal

from lxml import etree

PAGE_NS_MARKERS = (
    "primaresearch.org/PAGE",
    "pagecontent",
)

ALTO_NS_MARKERS = (
    "standards/alto",
    "http://www.loc.gov/standards/alto",
)


def detect_format(root: etree._Element) -> Literal["PAGE", "ALTO"] | None:
    tag = etree.QName(root).localname
    tag_l = tag.lower()
    ns = etree.QName(root).namespace or ""
    if tag_l == "alto" or any(m in ns for m in ALTO_NS_MARKERS):
        return "ALTO"
    if any(m in ns for m in PAGE_NS_MARKERS):
        return "PAGE"
    if "pcgtsdocument" in tag_l or tag_l == "pagedataset":
        return "PAGE"
    for child in root:
        ln = etree.QName(child).localname
        if ln == "Page":
            return "PAGE"
    return None


def local_name(el: etree._Element) -> str:
    return etree.QName(el).localname
