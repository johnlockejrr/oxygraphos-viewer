from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Literal

from lxml import etree

from app.utils.namespace import detect_format

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
XML_EXTENSIONS = {".xml"}


def _page_image_filename(xml_path: Path) -> str | None:
    try:
        tree = etree.parse(str(xml_path))
        root = tree.getroot()
        for el in root.iter():
            if etree.QName(el).localname == "Page":
                fn = el.get("imageFilename") or el.get("imagefilename")
                if fn:
                    return fn.strip()
    except Exception as e:
        logger.warning("Could not read PAGE imageFilename from %s: %s", xml_path, e)
    return None


def _alto_image_filename(xml_path: Path) -> str | None:
    try:
        tree = etree.parse(str(xml_path))
        root = tree.getroot()
        for el in root.iter():
            tag = etree.QName(el).localname.lower()
            if tag == "filename":
                t = (el.text or "").strip()
                if t:
                    return t
            fn = el.get("FILENAME") or el.get("fileName") or el.get("filename")
            if fn:
                return str(fn).strip()
    except Exception as e:
        logger.warning("Could not read ALTO fileName from %s: %s", xml_path, e)
    return None


def _detect_xml_format(xml_path: Path) -> Literal["PAGE", "ALTO"] | None:
    try:
        tree = etree.parse(str(xml_path))
        return detect_format(tree.getroot())
    except Exception:
        return None


def _find_image_in_dir(base_dir: Path, name: str, images_by_name: dict[str, Path]) -> Path | None:
    p = base_dir / name
    if p.is_file():
        return p.resolve()
    stem = Path(name).stem
    for ext in IMAGE_EXTENSIONS:
        cand = base_dir / f"{stem}{ext}"
        if cand.is_file():
            return cand.resolve()
    key = Path(name).name.lower()
    if key in images_by_name:
        return images_by_name[key]
    return None


def scan_directory(path: Path) -> list[tuple[Path, Path, Literal["PAGE", "ALTO"]]]:
    """
    Return list of (xml_path, image_path, format) for the given directory (non-recursive).
    """
    if not path.is_dir():
        return []

    xml_files: list[Path] = []
    image_files: list[Path] = []
    for child in sorted(path.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_file():
            continue
        suf = child.suffix.lower()
        if suf in XML_EXTENSIONS:
            xml_files.append(child)
        elif suf in IMAGE_EXTENSIONS:
            image_files.append(child)

    images_by_name = {p.name.lower(): p.resolve() for p in image_files}
    used_images: set[Path] = set()
    pairs: list[tuple[Path, Path, Literal["PAGE", "ALTO"]]] = []

    for xml_path in xml_files:
        fmt = _detect_xml_format(xml_path)
        if fmt is None:
            continue
        image_path: Path | None = None
        stem = xml_path.stem
        for ext in IMAGE_EXTENSIONS:
            cand = path / f"{stem}{ext}"
            if cand.is_file():
                image_path = cand.resolve()
                break
        if image_path is None:
            ref: str | None = None
            if fmt == "PAGE":
                ref = _page_image_filename(xml_path)
            else:
                ref = _alto_image_filename(xml_path)
            if ref:
                image_path = _find_image_in_dir(path, ref, images_by_name)
        if image_path and image_path not in used_images:
            used_images.add(image_path)
            pairs.append((xml_path.resolve(), image_path, fmt))

    paired_xml = {x[0] for x in pairs}
    unpaired_xml = [x for x in xml_files if x.resolve() not in paired_xml]
    unused_images = [p for p in image_files if p.resolve() not in used_images]
    if unpaired_xml and unused_images and len(unpaired_xml) == len(unused_images):
        for xml_path, img in zip(
            sorted(unpaired_xml, key=lambda p: p.name.lower()),
            sorted(unused_images, key=lambda p: p.name.lower()),
            strict=False,
        ):
            fmt = _detect_xml_format(xml_path)
            if fmt is None:
                continue
            ir = img.resolve()
            if ir not in used_images:
                used_images.add(ir)
                pairs.append((xml_path.resolve(), ir, fmt))

    pairs.sort(key=lambda t: t[0].name.lower())
    return pairs


def scan_directory_tree(root: Path) -> list[tuple[Path, Path, Literal["PAGE", "ALTO"]]]:
    """
    Walk `root` recursively and collect (xml, image, format) pairs from every directory.
    """
    root = root.resolve()
    if not root.is_dir():
        return []
    out: list[tuple[Path, Path, Literal["PAGE", "ALTO"]]] = []
    seen: set[tuple[Path, Path]] = set()
    for dirpath, _dirnames, _filenames in os.walk(root, topdown=True, followlinks=False):
        d = Path(dirpath)
        try:
            for triple in scan_directory(d):
                key = (triple[0].resolve(), triple[1].resolve())
                if key not in seen:
                    seen.add(key)
                    out.append(triple)
        except OSError as e:
            logger.debug("scan_directory_tree skip %s: %s", d, e)
    out.sort(key=lambda t: str(t[0]).lower())
    return out
