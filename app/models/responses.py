from pydantic import BaseModel


class DirEntry(BaseModel):
    name: str
    is_dir: bool
    path: str


class DirListingResponse(BaseModel):
    path: str
    entries: list[DirEntry]
    total: int
    page: int
    per_page: int
    pages: int


class SelectDirBody(BaseModel):
    path: str


class SelectDirResponse(BaseModel):
    valid: bool
    doc_count: int
    formats: list[str]


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
