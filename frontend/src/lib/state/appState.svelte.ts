import type { DocumentItem, DirListing, OverlayData } from '$lib/api/client';

export const appState = $state({
  currentDir: null as string | null,
  browsePath: null as string | null,
  dirEntries: null as DirListing | null,
  documents: [] as DocumentItem[],
  pagination: {
    page: 1,
    perPage: 20,
    total: 0,
    pages: 1,
  },
  activeDocId: null as string | null,
  overlayData: null as OverlayData | null,
  layers: {
    regions: true,
    textlines: true,
    baselines: true,
  },
  /** When true, mouse wheel over the main viewer zooms the page (scroll still works with trackpad gestures elsewhere). */
  viewerWheelZoom: false,
  loading: {
    dirs: false,
    docs: false,
    overlay: false,
  },
  errorMessage: null as string | null,
});
