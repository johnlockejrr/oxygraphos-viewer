# Oxygraphos Viewer

Production-oriented PAGE-XML / ALTO-XML viewer: **FastAPI** backend plus **SvelteKit** (Svelte 5) UI styled for the “Archival Dark” theme, with shadcn-style primitives (`components.json`, Tailwind tokens, `Button` / `Switch` / `ScrollArea` / `Skeleton`).

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or `pip`
- Node 20+ and npm (for the `frontend/` app)

## Backend

```bash
cd /path/to/Page-Viewer
uv pip install -r requirements.txt --python .venv/bin/python
PYTHONPATH=. uv run --python .venv/bin/python uvicorn app.main:app --reload --port 8000
```

Copy `.env.example` to `.env` and adjust `ALLOWED_ROOT` if needed.

## Frontend (development)

Vite proxies `/api` to `http://127.0.0.1:8000`.

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown (usually http://localhost:5173). Use **Use this folder** after browsing to a directory that contains paired XML + images.

## Production (single host)

1. Build the UI: `cd frontend && npm run build` (output in `frontend/build`).
2. Point `FRONTEND_DIST` in `.env` at the absolute path of `frontend/build`.
3. Run `uvicorn app.main:app --host 0.0.0.0 --port 8000` (or Gunicorn + Uvicorn workers per `AGENTS.md`).

## Tests

```bash
PYTHONPATH=. .venv/bin/pytest tests/ -v
```

## shadcn-svelte

The repo includes `frontend/components.json` and UI building blocks under `src/lib/components/ui/`. To regenerate or add official primitives once Node is available:

```bash
cd frontend
npx shadcn-svelte@latest init
# add components as needed, e.g. npx shadcn-svelte@latest add switch
```
