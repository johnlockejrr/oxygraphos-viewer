from typing import Literal, Optional

from pydantic import BaseModel, Field


class Point(BaseModel):
    x: float
    y: float


class BaselineData(BaseModel):
    id: str
    points: list[Point]


class TextLineData(BaseModel):
    id: str
    label: Optional[str] = None
    coords: list[Point]
    baseline: Optional[BaselineData] = None


class RegionData(BaseModel):
    id: str
    type: str
    label: Optional[str] = None
    coords: list[Point]
    textlines: list[TextLineData] = Field(default_factory=list)


class OverlayData(BaseModel):
    doc_id: str
    image_width: int
    image_height: int
    format: Literal["PAGE", "ALTO"]
    regions: list[RegionData]


class Document(BaseModel):
    id: str
    filename: str
    xml_path: str
    image_path: str
    format: Literal["PAGE", "ALTO"]
    thumb_url: str
    image_url: str
