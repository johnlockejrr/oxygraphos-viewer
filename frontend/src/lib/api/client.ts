export type DocumentItem = {
  id: string;
  filename: string;
  xml_path: string;
  image_path: string;
  format: 'PAGE' | 'ALTO';
  thumb_url: string;
  image_url: string;
};

export type DocsResponse = {
  total: number;
  page: number;
  per_page: number;
  pages: number;
  items: DocumentItem[];
};

export type DirEntry = {
  name: string;
  is_dir: boolean;
  path: string;
};

export type DirListing = {
  path: string;
  entries: DirEntry[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
};

export type Point = { x: number; y: number };

export type OverlayData = {
  doc_id: string;
  image_width: number;
  image_height: number;
  format: 'PAGE' | 'ALTO';
  regions: Array<{
    id: string;
    type: string;
    label?: string | null;
    coords: Point[];
    textlines: Array<{
      id: string;
      label?: string | null;
      coords: Point[];
      baseline?: { id: string; points: Point[] } | null;
    }>;
  }>;
};

function formatApiError(body: unknown): string {
  if (typeof body === 'string') return body;
  if (!body || typeof body !== 'object') return JSON.stringify(body);
  const o = body as Record<string, unknown>;
  const d = o.detail;
  if (typeof d === 'string') return d;
  if (d && typeof d === 'object') {
    const x = d as { error?: string; hint?: string; detail?: string };
    const parts = [x.error, x.hint ?? x.detail].filter(Boolean);
    if (parts.length) return parts.join(' — ');
  }
  return JSON.stringify(body);
}

async function parseJson<T>(r: Response): Promise<T> {
  if (!r.ok) {
    let body: unknown;
    try {
      body = await r.json();
    } catch {
      body = await r.text();
    }
    throw new Error(formatApiError(body));
  }
  return r.json() as Promise<T>;
}

export async function fetchDirs(
  path?: string,
  page: number = 1,
  perPage: number = 50,
): Promise<DirListing> {
  const params = new URLSearchParams();
  if (path) params.set('path', path);
  params.set('page', String(page));
  params.set('per_page', String(perPage));
  const q = params.toString();
  const r = await fetch(`/api/dirs?${q}`);
  return parseJson<DirListing>(r);
}

export async function selectDir(path: string): Promise<{ valid: boolean; doc_count: number; formats: string[] }> {
  const r = await fetch('/api/dirs/select', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  });
  return parseJson(r);
}

export async function fetchDocs(dir: string, page: number, perPage: number): Promise<DocsResponse> {
  const params = new URLSearchParams({
    dir,
    page: String(page),
    per_page: String(perPage),
  });
  const r = await fetch(`/api/docs?${params}`);
  return parseJson<DocsResponse>(r);
}

export async function fetchOverlay(docId: string, dir: string): Promise<OverlayData> {
  const params = new URLSearchParams({ dir });
  const r = await fetch(`/api/overlay/${encodeURIComponent(docId)}?${params}`);
  return parseJson<OverlayData>(r);
}
