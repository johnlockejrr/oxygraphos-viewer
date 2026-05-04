import logging

from app.models.document import Point

logger = logging.getLogger(__name__)


def normalize_points(raw: str, width: int, height: int) -> list[Point]:
    if width <= 0 or height <= 0:
        return []
    raw = (raw or "").strip()
    if not raw:
        return []
    out: list[Point] = []
    for pair in raw.split():
        parts = pair.split(",")
        if len(parts) != 2:
            continue
        try:
            x = float(parts[0]) / width
            y = float(parts[1]) / height
        except ValueError:
            logger.warning("Skipping malformed coordinate pair: %s", pair)
            continue
        out.append(Point(x=x, y=y))
    return out


def bbox_to_polygon(hpos: float, vpos: float, w: float, h: float) -> list[Point]:
    """Clockwise rectangle in normalized space; caller divides by page W/H first."""
    return [
        Point(x=hpos, y=vpos),
        Point(x=hpos + w, y=vpos),
        Point(x=hpos + w, y=vpos + h),
        Point(x=hpos, y=vpos + h),
    ]
