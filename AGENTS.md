# AGENTS.md — PAGE/ALTO XML Document Viewer

## Project Overview

Build a **production-ready Python web application** that allows a user to:
1. Select a local directory containing PAGE-XML or ALTO-XML files alongside their corresponding images
2. Browse documents as paginated thumbnails (IIIF-style left panel)
3. Click a thumbnail to open the document in a main viewer with SVG overlay rendering of:
   - **Regions** (TextRegion, ImageRegion, etc.)
   - **TextLines** (with baseline polylines)
   - **Baselines** (raw baseline points)
4. Toggle visibility of each overlay layer independently
5. Hover over any overlay to see the element's ID/type label from the XML
6. Enjoy a polished, professional, dark-themed responsive UI

---

## Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Backend | **FastAPI** (Python 3.11+) | Async, fast, automatic OpenAPI docs |
| XML Parsing | **lxml** | Robust XPath, namespace handling |
| Image serving | **FastAPI StaticFiles + custom route** | Range requests, thumbnail generation |
| Thumbnail generation | **Pillow** | Fast JPEG thumbnails cached on disk |
| Frontend | **Vanilla JS (ES modules) + CSS custom properties** | Zero build step, full control |
| Overlay rendering | **Inline SVG** positioned over `<img>` | No canvas needed, CSS transitions work |
| Fonts | **Google Fonts: Fraunces (display) + DM Mono (labels)** | Archival, scholarly, memorable |
| Deployment | **Uvicorn** (dev), **Gunicorn + Uvicorn workers** (prod) | Standard async Python serving |

---

## Project Structure

```
pageviewer/
├── AGENTS.md                  # This file
├── README.md
├── requirements.txt
├── pyproject.toml
├── .env.example
│
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI app factory, lifespan, router registration
│   ├── config.py              # Pydantic Settings (BASE_DIR, THUMB_CACHE, PAGE_SIZE)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── directories.py     # GET /api/dirs — directory browser endpoints
│   │   ├── documents.py       # GET /api/docs — list, paginate, metadata
│   │   └── overlays.py        # GET /api/overlay/{doc_id} — parsed XML overlay data
│   ├── services/
│   │   ├── __init__.py
│   │   ├── directory_scanner.py   # Scan dir, pair XML↔image files
│   │   ├── xml_parser.py          # PAGE-XML and ALTO-XML parsing → unified model
│   │   ├── thumbnail_service.py   # Generate/cache thumbnails with Pillow
│   │   └── image_service.py       # Serve original images, compute dimensions
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py        # Pydantic models: Document, OverlayData, Region, TextLine, Baseline
│   │   └── responses.py       # API response envelope models
│   └── utils/
│       ├── __init__.py
│       ├── namespace.py       # XML namespace constants for PAGE and ALTO
│       └── geometry.py        # Coordinate normalization helpers
│
├── static/
│   ├── css/
│   │   ├── reset.css
│   │   ├── variables.css      # CSS custom properties (colors, spacing, typography)
│   │   ├── layout.css         # App shell, panels, responsive grid
│   │   ├── thumbnails.css     # Thumbnail strip, active state, loading skeleton
│   │   ├── viewer.css         # Main viewer, SVG overlay styles, tooltip
│   │   └── controls.css       # Toggle switches, toolbar, pagination controls
│   └── js/
│       ├── app.js             # Entry point, state management, event wiring
│       ├── api.js             # Fetch wrappers for all API endpoints
│       ├── thumbnails.js      # Thumbnail panel rendering, pagination
│       ├── viewer.js          # Main viewer: image load, SVG overlay mount/unmount
│       ├── overlays.js        # SVG element creation for regions/textlines/baselines
│       ├── tooltip.js         # Hover tooltip positioning and content
│       └── controls.js        # Toggle switch logic, keyboard shortcuts
│
├── templates/
│   └── index.html             # Single-page app shell (Jinja2)
│
├── tests/
│   ├── conftest.py
│   ├── test_xml_parser.py
│   ├── test_directory_scanner.py
│   ├── test_api_documents.py
│   └── fixtures/
│       ├── sample_page.xml
│       ├── sample_alto.xml
│       └── sample_image.jpg
│
└── scripts/
    └── generate_test_fixtures.py
```

---

## Data Models

### Unified Overlay Model (app/models/document.py)

```python
from pydantic import BaseModel
from typing import Literal, Optional

class Point(BaseModel):
    x: float
    y: float

class BaselineData(BaseModel):
    id: str
    points: list[Point]          # polyline points

class TextLineData(BaseModel):
    id: str
    label: Optional[str]         # custom label or ID fallback
    coords: list[Point]          # polygon coords
    baseline: Optional[BaselineData]

class RegionData(BaseModel):
    id: str
    type: str                    # "TextRegion", "ImageRegion", "TableRegion", etc.
    label: Optional[str]         # custom label or type fallback
    coords: list[Point]          # polygon coords
    textlines: list[TextLineData]

class OverlayData(BaseModel):
    doc_id: str
    image_width: int
    image_height: int
    format: Literal["PAGE", "ALTO"]
    regions: list[RegionData]

class Document(BaseModel):
    id: str                      # slug derived from filename stem
    filename: str                # original filename without extension
    xml_path: str                # absolute path to XML
    image_path: str              # absolute path to image
    format: Literal["PAGE", "ALTO"]
    thumb_url: str               # /api/thumb/{doc_id}
    image_url: str               # /api/image/{doc_id}
```

---

## API Specification

### Directory Browser

```
GET /api/dirs?path={path}
```
- If `path` is omitted, return drives/home directory
- Returns: `{ "path": "/abs/path", "entries": [{ "name": str, "is_dir": bool, "path": str }] }`
- Security: Only allow browsing within `ALLOWED_ROOT` (configurable, defaults to home dir)

```
POST /api/dirs/select
Body: { "path": "/abs/path/to/directory" }
```
- Validates path exists and contains at least one XML+image pair
- Stores selected path in server session or returns it for client-side storage
- Returns: `{ "valid": bool, "doc_count": int, "formats": ["PAGE", "ALTO"] }`

### Documents

```
GET /api/docs?dir={path}&page={n}&per_page={n}
```
- `dir`: URL-encoded absolute path
- `page`: 1-based, default 1
- `per_page`: default 20, max 100
- Returns: `{ "total": int, "page": int, "per_page": int, "pages": int, "items": [Document] }`

### Overlays

```
GET /api/overlay/{doc_id}?dir={path}
```
- Parses XML file for `doc_id` in `dir`
- Returns: `OverlayData`
- Cache parsed result in memory (LRU, max 50 entries)

### Images & Thumbnails

```
GET /api/image/{doc_id}?dir={path}
```
- Streams original image with correct Content-Type
- Supports `Range` header for large images

```
GET /api/thumb/{doc_id}?dir={path}&size={150}
```
- Returns JPEG thumbnail (default 150px longest side)
- Cached to `THUMB_CACHE_DIR` (default `~/.pageviewer_cache/thumbs/`)
- Cache key: `{doc_id}_{mtime}_{size}.jpg`

---

## XML Parsing Requirements (app/services/xml_parser.py)

### PAGE-XML (http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15)

The parser must handle **multiple PAGE-XML schema versions** (2010, 2013, 2017, 2019). Use namespace-agnostic XPath or detect version from root namespace.

Extract:
- `//Page/@imageWidth`, `//Page/@imageHeight`
- `//TextRegion` → id, custom attribute (for label), `Coords/@points`
  - Each `TextLine` child → id, `Coords/@points`, `Baseline/@points`
- `//ImageRegion`, `//TableRegion`, `//SeparatorRegion`, `//GraphicRegion`, `//ChartRegion`, `//MathsRegion`, `//ChemRegion`, `//MusicRegion`, `//AdvertRegion`, `//NoiseRegion`, `//UnknownRegion`
  - Only top-level coords, no textlines

Coordinate format: `"x1,y1 x2,y2 x3,y3 ..."` space-separated pairs.

### ALTO-XML (http://www.loc.gov/standards/alto/)

Handle ALTO 2.x, 3.x, 4.x. All use `alto` namespace but URI varies. Detect version.

Extract:
- `//Layout/Page/@WIDTH`, `//Layout/Page/@HEIGHT`
- `//PrintSpace//TextBlock` → ID, `HPOS`, `VPOS`, `WIDTH`, `HEIGHT` → convert to polygon `[x,y, x+w,y, x+w,y+h, x,y+h]`
  - Each `TextLine` child → same HPOS/VPOS/WIDTH/HEIGHT bounding box conversion
    - Each `String/@CONTENT` for label fallback

Label resolution priority:
1. PAGE: `@custom` attribute value (if it contains `type:` prefix, strip it)
2. PAGE: `@id` attribute
3. ALTO: `@TAGREFS` resolved to `<Tag LABEL=...>` in header
4. ALTO: element `@ID`

### Coordinate Normalization

All coordinates must be returned as **normalized floats (0.0–1.0)** relative to image dimensions. This makes the SVG overlay resolution-independent.

```python
def normalize_points(raw: str, width: int, height: int) -> list[Point]:
    pairs = raw.strip().split()
    return [Point(x=float(p.split(",")[0])/width, y=float(p.split(",")[1])/height) for p in pairs]
```

---

## Frontend Architecture

### State (app.js)

```javascript
const state = {
  currentDir: null,          // absolute path string
  documents: [],             // Document[]
  pagination: { page: 1, perPage: 20, total: 0, pages: 0 },
  activeDocId: null,         // currently opened document
  overlayData: null,         // OverlayData for active doc
  imageSize: { w: 0, h: 0 }, // rendered image size (px)
  layers: {
    regions: true,
    textlines: true,
    baselines: true,
  },
};
```

### Viewer Overlay Rendering (overlays.js)

- Mount a single `<svg>` element absolutely over the `<img>` using CSS `position: absolute; inset: 0`
- SVG `viewBox` = `"0 0 1 1"` (normalized coordinate space)
- SVG `preserveAspectRatio="none"` — scale with image
- For each **Region**: `<polygon points="..." class="overlay-region overlay-region--{type}" data-label="{label}">`
- For each **TextLine**: `<polygon points="..." class="overlay-textline" data-label="{label}">`
- For each **Baseline**: `<polyline points="..." class="overlay-baseline" data-label="{label}">`
- Group each type in `<g class="layer-regions">`, `<g class="layer-textlines">`, `<g class="layer-baselines">`
- Toggle visibility with `<g>.style.display = show ? '' : 'none'`

### Tooltip (tooltip.js)

- Single `<div id="tooltip">` fixed-position, hidden by default
- On `mousemove` over SVG elements with `data-label`: show tooltip near cursor
- On `mouseleave` from SVG: hide tooltip
- Tooltip shows: element type badge + label/ID text
- Fade in/out with CSS transition `opacity 120ms ease`

### Thumbnail Panel (thumbnails.js)

- Left panel: scrollable vertical list of thumbnail cards
- Each card: `<img src="{thumb_url}">` + filename label
- Lazy-load thumbnails using `IntersectionObserver`
- Active card: highlighted left border accent + subtle glow
- Pagination: Prev / Page N of M / Next at panel bottom
- Keyboard: ArrowUp/ArrowDown navigate between thumbnails, Enter opens

### Responsive Layout

```
Desktop (>= 1024px): Left panel 260px fixed | Main viewer fills rest
Tablet (768–1023px): Left panel 200px | Main viewer fills rest  
Mobile (< 768px):    Bottom sheet thumbnail strip (horizontal scroll) | Viewer full height
```

---

## Visual Design Specification

### Theme: "Archival Dark" — scholarly, precise, atmospheric

```css
/* variables.css */
:root {
  /* Backgrounds */
  --bg-void: #0a0a0c;
  --bg-surface: #111115;
  --bg-panel: #16161b;
  --bg-card: #1c1c23;
  --bg-card-hover: #222230;

  /* Borders */
  --border-subtle: rgba(255,255,255,0.06);
  --border-accent: rgba(255,255,255,0.12);

  /* Typography */
  --text-primary: #e8e6e0;
  --text-secondary: #8b8a85;
  --text-muted: #55544f;

  /* Accents */
  --accent-amber: #d4a84b;        /* primary accent — parchment gold */
  --accent-amber-dim: #8a6c2e;
  --accent-teal: #3d9e8c;         /* secondary — ink teal */
  --accent-rose: #c4605a;         /* warning/error */

  /* Overlay colors */
  --overlay-region: rgba(212, 168, 75, 0.18);
  --overlay-region-stroke: rgba(212, 168, 75, 0.7);
  --overlay-region-hover: rgba(212, 168, 75, 0.35);
  --overlay-textline: rgba(61, 158, 140, 0.15);
  --overlay-textline-stroke: rgba(61, 158, 140, 0.65);
  --overlay-textline-hover: rgba(61, 158, 140, 0.30);
  --overlay-baseline: rgba(196, 96, 90, 0.9);

  /* Spacing scale */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;

  /* Typography */
  --font-display: 'Fraunces', Georgia, serif;
  --font-body: 'DM Mono', 'Courier New', monospace;
  --font-ui: 'DM Mono', monospace;

  /* Radius */
  --radius-sm: 3px;
  --radius-md: 6px;
  --radius-lg: 12px;

  /* Shadows */
  --shadow-card: 0 1px 3px rgba(0,0,0,0.4), 0 4px 12px rgba(0,0,0,0.3);
  --shadow-elevated: 0 8px 32px rgba(0,0,0,0.6);
}
```

### Typography

Load from Google Fonts:
```html
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,300;0,400;0,600;1,300&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
```

- App title: `Fraunces 300` — "Oxygraphos Viewer"
- Filename labels: `DM Mono 400` 11px, letter-spacing 0.04em
- Tooltip text: `DM Mono 400` 12px
- Controls/buttons: `DM Mono 500` 11px uppercase letter-spacing 0.08em
- Page count: `DM Mono 300`

### Overlay SVG Styles

```css
.overlay-region {
  fill: var(--overlay-region);
  stroke: var(--overlay-region-stroke);
  stroke-width: 0.002;
  cursor: crosshair;
  transition: fill 120ms ease;
}
.overlay-region:hover { fill: var(--overlay-region-hover); }

.overlay-textline {
  fill: var(--overlay-textline);
  stroke: var(--overlay-textline-stroke);
  stroke-width: 0.0015;
  cursor: crosshair;
  transition: fill 120ms ease;
}
.overlay-textline:hover { fill: var(--overlay-textline-hover); }

.overlay-baseline {
  fill: none;
  stroke: var(--overlay-baseline);
  stroke-width: 0.002;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* Layer group transitions */
.layer-regions, .layer-textlines, .layer-baselines {
  transition: opacity 200ms ease;
}
.layer-regions.hidden, .layer-textlines.hidden, .layer-baselines.hidden {
  opacity: 0;
  pointer-events: none;
}
```

### Toggle Controls

Custom toggle switches (no checkbox hack — use `role="switch"` button):
```
[●●●] Regions     [●●●] TextLines     [●●●] Baselines
```
Each switch: pill shape, active = amber fill, inactive = dark fill, animated knob slide.

### Thumbnail Card

```
┌─────────────────┐
│                 │
│   [thumbnail]   │  ← 150×200px max, object-fit: contain, bg #0a0a0c
│                 │
└─────────────────┘
  filename.xml         ← truncated, DM Mono 10px
```

Active state: 2px left border in `--accent-amber`, card background `--bg-card-hover`, soft glow `box-shadow: -2px 0 0 var(--accent-amber), 0 0 20px rgba(212,168,75,0.1)`.

Loading skeleton: animated gradient shimmer using `@keyframes shimmer`.

---

## Backend Implementation Details

### app/main.py

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routers import directories, documents, overlays
from app.config import settings
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.THUMB_CACHE_DIR, exist_ok=True)
    yield

app = FastAPI(title="Oxygraphos Viewer", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.include_router(directories.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(overlays.router, prefix="/api")

@app.get("/")
async def index(request):
    return templates.TemplateResponse("index.html", {"request": request})
```

### app/config.py

```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    ALLOWED_ROOT: Path = Path.home()
    THUMB_CACHE_DIR: Path = Path.home() / ".pageviewer_cache" / "thumbs"
    THUMB_SIZE: int = 150
    PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    OVERLAY_CACHE_SIZE: int = 50

    class Config:
        env_file = ".env"

settings = Settings()
```

### app/services/directory_scanner.py

```python
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
XML_EXTENSIONS = {".xml"}

def scan_directory(path: Path) -> list[tuple[Path, Path]]:
    """
    Return list of (xml_path, image_path) pairs found in directory.
    Matching strategy:
    1. Same stem: page_001.xml + page_001.jpg
    2. XML contains <Page imageFilename="..."> or ALTO <fileName> → resolve relative to dir
    3. Fallback: alphabetical order pairing
    """
```

### app/services/xml_parser.py

```python
from lxml import etree
from app.models.document import OverlayData, RegionData, TextLineData, BaselineData, Point
from app.utils.namespace import detect_format, get_namespaces

PAGE_REGION_TYPES = [
    "TextRegion", "ImageRegion", "TableRegion", "SeparatorRegion",
    "GraphicRegion", "ChartRegion", "MathsRegion", "ChemRegion",
    "MusicRegion", "AdvertRegion", "NoiseRegion", "UnknownRegion"
]

def parse_xml(xml_path: Path, image_path: Path) -> OverlayData:
    tree = etree.parse(str(xml_path))
    root = tree.getroot()
    fmt = detect_format(root)
    if fmt == "PAGE":
        return _parse_page(root, xml_path, image_path)
    elif fmt == "ALTO":
        return _parse_alto(root, xml_path, image_path)
    raise ValueError(f"Unknown XML format in {xml_path}")
```

**Critical parsing notes:**
- Always use `lxml`'s Clark notation for namespaces: `{http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15}TextRegion`
- Strip namespace from tag for type extraction: `etree.QName(el.tag).localname`
- Handle missing `@imageWidth`/`@imageHeight` by reading actual image dimensions with Pillow as fallback
- If `Coords/@points` is empty or malformed, skip element with a warning log
- ALTO bounding box to polygon: always produce 4-point clockwise polygon

### app/services/thumbnail_service.py

```python
from PIL import Image
from pathlib import Path
import hashlib

def get_thumbnail(image_path: Path, size: int, cache_dir: Path) -> Path:
    mtime = int(image_path.stat().st_mtime)
    key = hashlib.md5(f"{image_path}{mtime}{size}".encode()).hexdigest()
    cache_path = cache_dir / f"{key}.jpg"
    if cache_path.exists():
        return cache_path
    with Image.open(image_path) as img:
        img.thumbnail((size, size * 2), Image.LANCZOS)
        img = img.convert("RGB")
        img.save(cache_path, "JPEG", quality=85, optimize=True)
    return cache_path
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Directory not found | 404 with `{"error": "directory_not_found"}` |
| XML parse error | 422 with `{"error": "xml_parse_error", "detail": "..."}`, skip document in listing |
| Image not found | 404, thumbnail shows placeholder SVG |
| No XML+image pairs found | 400 with `{"error": "no_documents_found"}` |
| Unsupported XML format | 422 with `{"error": "unsupported_format"}` |
| Path traversal attempt | 403 with `{"error": "access_denied"}` |

**Security**: All path inputs must be validated against `ALLOWED_ROOT`. Use `path.resolve().is_relative_to(settings.ALLOWED_ROOT)` check on every file access.

---

## Performance Requirements

- Thumbnail generation: async, using `asyncio.to_thread` for Pillow (blocking I/O)
- XML parsing: LRU-cached in memory (max 50 entries), re-parse on file mtime change
- Thumbnail serving: set `Cache-Control: public, max-age=86400`
- Image serving: set `Cache-Control: public, max-age=3600`
- Frontend: thumbnails lazy-loaded via `IntersectionObserver`
- SVG overlays: built with `DocumentFragment` before DOM insertion (single reflow)
- Tooltip: debounced mousemove handler (16ms / ~60fps)

---

## Accessibility

- Thumbnail list: `role="listbox"`, each item `role="option"`, `aria-selected`
- Layer toggles: `role="switch"`, `aria-checked`, `aria-label`
- Tooltip: `role="tooltip"`, `aria-live="polite"` on container
- Keyboard: Tab navigates controls; Arrow keys navigate thumbnail list; `1`/`2`/`3` keys toggle layers; `←`/`→` paginate
- Focus visible: custom focus ring in `--accent-amber`

---

## requirements.txt

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
lxml>=5.2.0
Pillow>=10.3.0
python-multipart>=0.0.9
jinja2>=3.1.4
aiofiles>=23.2.1
cachetools>=5.3.3
```

---

## Development Setup

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment config
cp .env.example .env
# Edit ALLOWED_ROOT if needed

# 4. Run development server
uvicorn app.main:app --reload --port 8000

# 5. Open browser
open http://localhost:8000
```

---

## Testing Requirements

All tests in `tests/` using **pytest** + **httpx** (async test client).

### Required test coverage:

- `test_xml_parser.py`:
  - Parse PAGE-XML 2019 fixture → correct region count, coordinate values
  - Parse ALTO-XML 4.x fixture → correct block count, bounding box conversion
  - Handle malformed XML gracefully (no exception, log warning)
  - Coordinate normalization accuracy (within 0.001 float tolerance)

- `test_directory_scanner.py`:
  - Scan directory with matching stems → correct pairs
  - Scan directory with `imageFilename` attribute → correct pairs
  - Empty directory → empty list, no exception
  - Mixed PAGE and ALTO in same dir → both detected

- `test_api_documents.py`:
  - `GET /api/docs` with valid dir → 200, correct pagination
  - `GET /api/docs?page=999` → empty items, 200
  - `GET /api/overlay/{id}` → 200, valid OverlayData schema
  - Path traversal attempt → 403
  - Non-existent directory → 404

---

## Production Deployment

```bash
# Gunicorn with Uvicorn workers
gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -w 4 \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --access-logfile -
```

Optional: Add nginx reverse proxy in front for static file serving and SSL termination.

---

## Implementation Order for Agent

Execute in this exact order:

1. **Scaffold** project structure (all dirs, empty `__init__.py` files)
2. **Models** (`app/models/document.py`, `app/models/responses.py`)
3. **Config** (`app/config.py`)
4. **Utils** (`app/utils/namespace.py`, `app/utils/geometry.py`)
5. **Services** in order: `directory_scanner.py` → `xml_parser.py` → `thumbnail_service.py` → `image_service.py`
6. **Routers** in order: `directories.py` → `documents.py` → `overlays.py`
7. **App factory** (`app/main.py`)
8. **Templates** (`templates/index.html`)
9. **CSS** in order: `reset.css` → `variables.css` → `layout.css` → `thumbnails.css` → `viewer.css` → `controls.css`
10. **JavaScript** in order: `api.js` → `tooltip.js` → `controls.js` → `overlays.js` → `viewer.js` → `thumbnails.js` → `app.js`
11. **Test fixtures** and **test files**
12. **README.md** with screenshots placeholder
13. **Final integration test**: run server, verify all API endpoints, verify overlay rendering in browser

---

## Definition of Done

- [ ] Server starts with `uvicorn app.main:app --reload` with no errors
- [ ] Directory browser allows selecting any directory within ALLOWED_ROOT
- [ ] Documents list paginates correctly at 20 per page
- [ ] Thumbnails load with lazy-loading and show filename
- [ ] Clicking thumbnail loads image in main viewer
- [ ] PAGE-XML regions render as amber polygons
- [ ] PAGE-XML textlines render as teal polygons
- [ ] PAGE-XML baselines render as rose polylines
- [ ] ALTO-XML blocks and textlines render correctly
- [ ] All three layer toggles work independently
- [ ] Hovering any overlay element shows correct label/ID tooltip
- [ ] Keyboard shortcuts (1/2/3, arrows) work
- [ ] Layout is responsive at 375px, 768px, 1280px, 1920px viewport widths
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No path traversal vulnerabilities
- [ ] Thumbnail cache persists between server restarts
