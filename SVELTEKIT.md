I hear you. Replacing a 700-line document with a 200-line summary is definitely not what you asked for. If we want to keep the original backend logic intact but swap the "brain" and "skin" of the frontend, here is the dedicated **SvelteKit + shadcn-svelte** continuation.

You can append this directly to your existing `AGENTS.md` or use it to replace the "Frontend Architecture" and "Visual Design" sections.

---

## Frontend Implementation: SvelteKit + shadcn-svelte

This section replaces the previous Vanilla JS implementation with a modern, reactive architecture using **Svelte 5 (Runes)** and **shadcn-svelte** primitives.

### 1. Updated Frontend Project Structure
```text
frontend/
├── src/
│   ├── lib/
│   │   ├── components/
│   │   │   ├── viewer/
│   │   │   │   ├── ImageViewer.svelte    # Main SVG + Img container
│   │   │   │   ├── OverlayLayer.svelte   # Reactive SVG paths/polygons
│   │   │   │   └── TooltipLabel.svelte   # shadcn-based hover labels
│   │   │   ├── sidebar/
│   │   │   │   ├── ThumbnailCard.svelte  # Lazy-loaded thumb with active state
│   │   │   │   └── Pagination.svelte     # shadcn-svelte pagination controls
│   │   │   └── controls/
│   │   │       └── LayerToggles.svelte   # shadcn-svelte Switch components
│   │   ├── state/
│   │   │   └── appState.svelte.ts        # Global reactive state using Runes
│   │   └── api/
│   │       └── client.ts                 # Typed fetch wrappers for FastAPI
│   └── routes/
│       └── +page.svelte                  # Main Application Layout
├── tailwind.config.ts                    # "Archival Dark" theme definitions
└── svelte.config.js
```

---

### 2. Reactive State Management (Svelte 5 Runes)
We replace manual state objects with Svelte 5's `$state` for fine-grained updates without re-rendering the entire DOM[cite: 1].

```typescript
// src/lib/state/appState.svelte.ts
export const appState = $state({
  currentDir: null as string | null,
  documents: [] as any[],
  activeDoc: null as any | null,
  overlayData: null as any | null, // Stores PAGE/ALTO coordinates
  pagination: { page: 1, perPage: 20, total: 0 },
  
  // Layer visibility toggles
  layers: {
    regions: true,
    textlines: true,
    baselines: false
  },

  // Derived state for pagination
  get totalPages() {
    return Math.ceil(this.pagination.total / this.pagination.perPage);
  }
});
```

---

### 3. SVG Overlay Rendering Logic
The SVG uses the normalized coordinates (0.0–1.0) provided by the backend to remain resolution-independent[cite: 1].

*   **Viewbox**: Set to `0 0 1 1` with `preserveAspectRatio="none"` to stretch exactly over the `<img>`[cite: 1].
*   **Reactivity**: Svelte's `{#each}` blocks render `RegionData`, `TextLineData`, and `BaselineData` as they arrive from the API[cite: 1].

```svelte
<!-- src/lib/components/viewer/OverlayLayer.svelte -->
<svg viewBox="0 0 1 1" class="absolute inset-0 h-full w-full pointer-events-none">
  {#if appState.layers.regions}
    {#each appState.overlayData.regions as region}
      <polygon
        points={region.coords.map(p => `${p.x},${p.y}`).join(' ')}
        class="pointer-events-auto fill-amber-500/10 stroke-amber-500/50 hover:fill-amber-500/30 transition-colors"
      >
        <title>{region.label || region.id}</title>
      </polygon>
    {/each}
  {/if}
</svg>
```

---

### 4. Visual Design Integration (Archival Dark)
We map the original "Archival Dark" color palette[cite: 1] into the `tailwind.config.ts` using shadcn's CSS variable system.

*   **Colors**:
    *   `--background`: `#0a0a0c` (The Void)[cite: 1].
    *   `--primary`: `#d4a84b` (Parchment Gold)[cite: 1].
    *   `--secondary`: `#3d9e8c` (Ink Teal)[cite: 1].
    *   `--accent-rose`: `#c4605a` (Baseline Red)[cite: 1].
*   **Typography**:
    *   **Serif**: `Fraunces` for scholarly display text[cite: 1].
    *   **Mono**: `DM Mono` for technical labels and XML IDs[cite: 1].

---

### 5. Enhanced Interaction Patterns
*   **Smooth Toggles**: Use shadcn-svelte `Switch` components with spring animations for layer visibility[cite: 1].
*   **Tooltips**: Instead of a custom `div`, use shadcn's `Tooltip` primitive which handles collision detection and ARIA roles automatically[cite: 1].
*   **Keyboard Navigation**: Svelte `onkeydown` listeners on the window to capture `1`, `2`, `3` keys for layer toggling and Arrow keys for pagination[cite: 1].
*   **Thumbnail Skeletons**: Use shadcn `Skeleton` components during `GET /api/docs` fetches to prevent layout shift[cite: 1].

---

### 6. Updated Implementation Order (Frontend Only)
1.  **Initialize SvelteKit**: Setup with TypeScript and Tailwind CSS.
2.  **Add shadcn-svelte**: Install `Button`, `Switch`, `ScrollArea`, `Tooltip`, and `Skeleton`.
3.  **Theme Config**: Add "Archival Dark" hex codes to `app.css` and `tailwind.config.ts`[cite: 1].
4.  **Api Client**: Create the fetcher for FastAPI endpoints using the `ALLOWED_ROOT` security patterns[cite: 1].
5.  **State Store**: Implement the Svelte 5 `appState` rune.
6.  **Sidebar Components**: Build the thumbnail list with `IntersectionObserver` for lazy loading[cite: 1].
7.  **SVG Viewer**: Build the SVG coordinate mapping logic[cite: 1].
8.  **Main Layout**: Assemble the responsive grid (Sidebar | Viewer)[cite: 1].
