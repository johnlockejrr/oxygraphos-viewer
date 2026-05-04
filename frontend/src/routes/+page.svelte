<script lang="ts">
  import { onMount } from 'svelte';
  import { fetchDirs, fetchDocs, fetchOverlay, selectDir } from '$lib/api/client';
  import type { DocumentItem } from '$lib/api/client';
  import { appState } from '$lib/state/appState.svelte';
  import { Button } from '$lib/components/ui/button';
  import ScrollArea from '$lib/components/ui/scroll-area/scroll-area.svelte';
  import Skeleton from '$lib/components/ui/skeleton/skeleton.svelte';
  import ThumbnailCard from '$lib/components/sidebar/ThumbnailCard.svelte';
  import PaginationBar from '$lib/components/sidebar/PaginationBar.svelte';
  import LayerToggles from '$lib/components/controls/LayerToggles.svelte';
  import ImageViewer from '$lib/components/viewer/ImageViewer.svelte';
  import TooltipHud from '$lib/components/viewer/TooltipHud.svelte';

  let thumbFocus = $state(0);
  let rafHover = 0;

  let tip = $state({
    visible: false,
    x: 0,
    y: 0,
    title: '',
    body: '',
  });

  function showTip(title: string, body: string, ev: MouseEvent) {
    cancelAnimationFrame(rafHover);
    rafHover = requestAnimationFrame(() => {
      tip = { visible: true, x: ev.clientX, y: ev.clientY, title, body };
    });
  }

  function hideTip() {
    cancelAnimationFrame(rafHover);
    tip = { ...tip, visible: false };
  }

  type BrowseOpts = {
    /** Use server default root (BROWSE_START_PATH / ALLOWED_ROOT) */
    resetToRoot?: boolean;
    /** Open this folder; defaults to page 1 when set */
    path?: string;
    /** Page within current or given folder */
    page?: number;
  };

  async function loadBrowse(opts?: BrowseOpts) {
    const page = opts?.page ?? 1;
    let pathForApi: string | undefined;
    if (opts?.resetToRoot) {
      pathForApi = undefined;
    } else if (opts?.path !== undefined) {
      pathForApi = opts.path;
    } else {
      pathForApi = appState.browsePath ?? undefined;
    }
    const perPage = appState.dirEntries?.per_page ?? 50;
    appState.loading.dirs = true;
    appState.errorMessage = null;
    try {
      const listing = await fetchDirs(pathForApi, page, perPage);
      appState.dirEntries = listing;
      appState.browsePath = listing.path;
    } catch (e) {
      appState.errorMessage = e instanceof Error ? e.message : String(e);
    } finally {
      appState.loading.dirs = false;
    }
  }

  async function confirmFolder() {
    const p = appState.browsePath;
    if (!p) return;
    appState.errorMessage = null;
    try {
      await selectDir(p);
    } catch (e) {
      appState.errorMessage = e instanceof Error ? e.message : String(e);
      return;
    }
    appState.currentDir = p;
    appState.pagination.page = 1;
    await loadDocuments();
  }

  async function loadDocuments() {
    const dir = appState.currentDir;
    if (!dir) return;
    appState.loading.docs = true;
    try {
      const res = await fetchDocs(dir, appState.pagination.page, appState.pagination.perPage);
      appState.documents = res.items;
      appState.pagination.total = res.total;
      appState.pagination.pages = res.pages;
      appState.pagination.perPage = res.per_page;
    } catch (e) {
      appState.errorMessage = e instanceof Error ? e.message : String(e);
    } finally {
      appState.loading.docs = false;
    }
  }

  async function openDocument(doc: DocumentItem) {
    const dir = appState.currentDir;
    if (!dir) return;
    appState.activeDocId = doc.id;
    appState.loading.overlay = true;
    appState.errorMessage = null;
    try {
      appState.overlayData = await fetchOverlay(doc.id, dir);
    } catch (e) {
      appState.errorMessage = e instanceof Error ? e.message : String(e);
      appState.overlayData = null;
    } finally {
      appState.loading.overlay = false;
    }
  }

  function onKeydown(ev: KeyboardEvent) {
    if (ev.target instanceof HTMLInputElement || ev.target instanceof HTMLTextAreaElement) return;
    if (ev.key === '1') {
      appState.layers.regions = !appState.layers.regions;
      ev.preventDefault();
    } else if (ev.key === '2') {
      appState.layers.textlines = !appState.layers.textlines;
      ev.preventDefault();
    } else if (ev.key === '3') {
      appState.layers.baselines = !appState.layers.baselines;
      ev.preventDefault();
    } else if (ev.key === 'ArrowLeft' && appState.currentDir) {
      if (appState.pagination.page > 1) {
        appState.pagination.page -= 1;
        void loadDocuments();
      }
      ev.preventDefault();
    } else if (ev.key === 'ArrowRight' && appState.currentDir) {
      if (appState.pagination.page < appState.pagination.pages) {
        appState.pagination.page += 1;
        void loadDocuments();
      }
      ev.preventDefault();
    } else if (ev.key === 'ArrowUp') {
      thumbFocus = Math.max(0, thumbFocus - 1);
      const d = appState.documents[thumbFocus];
      if (d) void openDocument(d);
      ev.preventDefault();
    } else if (ev.key === 'ArrowDown') {
      thumbFocus = Math.min(appState.documents.length - 1, thumbFocus + 1);
      const d = appState.documents[thumbFocus];
      if (d) void openDocument(d);
      ev.preventDefault();
    } else if (ev.key === 'Enter' && appState.documents[thumbFocus]) {
      void openDocument(appState.documents[thumbFocus]);
      ev.preventDefault();
    }
  }

  onMount(() => {
    void loadBrowse({ resetToRoot: true });
    window.addEventListener('keydown', onKeydown);
    return () => window.removeEventListener('keydown', onKeydown);
  });

  $effect(() => {
    if (appState.documents.length && appState.activeDocId) {
      const idx = appState.documents.findIndex((d) => d.id === appState.activeDocId);
      if (idx >= 0) thumbFocus = idx;
    }
  });

  const imageSrc = $derived.by(() => {
    const dir = appState.currentDir;
    const id = appState.activeDocId;
    if (!dir || !id) return '';
    const doc = appState.documents.find((d) => d.id === id);
    return doc?.image_url ?? '';
  });

  function parentPath(abs: string): string | undefined {
    const trimmed = abs.replace(/[/\\]+$/, '');
    const i = Math.max(trimmed.lastIndexOf('/'), trimmed.lastIndexOf('\\'));
    if (i <= 0) return undefined;
    return trimmed.slice(0, i);
  }
</script>

<div class="flex min-h-screen flex-col bg-background text-foreground">
  <header class="border-b border-white/10 bg-card/40 px-4 py-4 backdrop-blur">
    <div class="mx-auto flex max-w-[1600px] flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="font-display text-2xl font-light tracking-tight text-primary md:text-3xl">Oxygraphos Viewer</h1>
        <p class="mt-1 max-w-xl text-[12px] text-muted-foreground">
          PAGE / ALTO overlays with archival dark UI. Run the API on port 8000; Vite proxies <code class="text-primary">/api</code>.
        </p>
      </div>
      <LayerToggles bind:layers={appState.layers} />
    </div>
  </header>

  <section class="border-b border-white/10 bg-muted/20 px-4 py-3">
    <div class="mx-auto flex max-w-[1600px] flex-col gap-2">
      <div class="flex flex-wrap items-center gap-2 text-[11px] uppercase tracking-[0.08em] text-muted-foreground">
        <span class="font-mono text-[10px] normal-case text-foreground">{appState.browsePath ?? '…'}</span>
        {#if appState.currentDir}
          <span class="rounded bg-primary/20 px-2 py-0.5 text-primary">Open: {appState.currentDir}</span>
        {/if}
      </div>
      {#if appState.loading.dirs}
        <Skeleton class="h-16 w-full" />
      {:else if appState.dirEntries}
        <p class="font-mono text-[10px] text-muted-foreground">
          Showing
          {#if appState.dirEntries.total > 0}
            {(appState.dirEntries.page - 1) * appState.dirEntries.per_page + 1}–{Math.min(
              appState.dirEntries.page * appState.dirEntries.per_page,
              appState.dirEntries.total,
            )}
            of {appState.dirEntries.total}
          {:else}
            0 of 0
          {/if}
          · page {appState.dirEntries.page} / {appState.dirEntries.pages}
        </p>
        <div class="flex max-h-[40vh] flex-wrap gap-2 overflow-y-auto">
          {#each appState.dirEntries.entries as entry (entry.path)}
            <Button
              variant="outline"
              type="button"
              onclick={() => {
                if (entry.is_dir) void loadBrowse({ path: entry.path, page: 1 });
              }}
            >
              {entry.is_dir ? '📁' : '📄'} {entry.name}
            </Button>
          {/each}
        </div>
        {#if appState.dirEntries.pages > 1}
          <div class="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              type="button"
              disabled={appState.dirEntries.page <= 1}
              onclick={() => void loadBrowse({ page: appState.dirEntries.page - 1 })}
            >
              Folder prev
            </Button>
            <span class="font-mono text-[10px] text-muted-foreground">
              {appState.dirEntries.page} / {appState.dirEntries.pages}
            </span>
            <Button
              variant="outline"
              type="button"
              disabled={appState.dirEntries.page >= appState.dirEntries.pages}
              onclick={() => void loadBrowse({ page: appState.dirEntries.page + 1 })}
            >
              Folder next
            </Button>
          </div>
        {/if}
        <div class="flex flex-wrap gap-2">
          <Button type="button" onclick={() => void loadBrowse({ resetToRoot: true })}>Home</Button>
          <Button
            type="button"
            onclick={() => {
              const p = appState.browsePath;
              if (!p) return;
              const up = parentPath(p);
              if (up !== undefined) void loadBrowse({ path: up, page: 1 });
              else void loadBrowse({ resetToRoot: true });
            }}
          >
            Up
          </Button>
          <Button type="button" onclick={() => void confirmFolder()}>Use this folder</Button>
        </div>
      {/if}
    </div>
  </section>

  {#if appState.errorMessage}
    <div class="mx-auto w-full max-w-[1600px] px-4 py-2 text-sm text-destructive">{appState.errorMessage}</div>
  {/if}

  <main class="mx-auto flex w-full max-w-[1600px] flex-1 flex-col gap-4 px-2 py-4 lg:flex-row">
    <div
      class="flex w-full flex-col rounded-lg border border-white/10 bg-card/40 lg:w-[280px] xl:w-[300px]"
      role="listbox"
      aria-label="Documents"
    >
      <div class="border-b border-white/10 px-3 py-2 font-mono text-[11px] text-muted-foreground">
        Thumbnails · <span class="text-foreground">{appState.pagination.total}</span> docs
      </div>
      {#if appState.loading.docs}
        <div class="space-y-2 p-2">
          {#each Array(4) as _, i (i)}
            <Skeleton class="h-36 w-full" />
          {/each}
        </div>
      {:else}
        <ScrollArea class="max-h-[70vh] flex-1 p-2 lg:max-h-[calc(100vh-220px)]">
          <div class="flex flex-col gap-2">
            {#each appState.documents as doc (doc.id)}
              <ThumbnailCard {doc} active={doc.id === appState.activeDocId} onSelect={() => openDocument(doc)} />
            {/each}
          </div>
        </ScrollArea>
        <PaginationBar
          page={appState.pagination.page}
          pages={appState.pagination.pages}
          onPrev={() => {
            if (appState.pagination.page > 1) {
              appState.pagination.page -= 1;
              void loadDocuments();
            }
          }}
          onNext={() => {
            if (appState.pagination.page < appState.pagination.pages) {
              appState.pagination.page += 1;
              void loadDocuments();
            }
          }}
        />
      {/if}
    </div>

    <section class="flex min-h-[50vh] flex-1 flex-col rounded-lg border border-white/10 bg-card/20 p-3">
      {#if imageSrc}
        <div class="mb-2 flex flex-wrap items-center gap-2">
          <Button
            variant={appState.viewerWheelZoom ? 'default' : 'outline'}
            type="button"
            class="!px-3 !py-1 text-[10px]"
            onclick={() => (appState.viewerWheelZoom = !appState.viewerWheelZoom)}
          >
            {appState.viewerWheelZoom ? 'Wheel zoom: on' : 'Wheel zoom: off'}
          </Button>
        </div>
      {/if}
      {#if appState.loading.overlay}
        <div class="text-sm text-muted-foreground">Loading overlay…</div>
      {/if}
      {#if imageSrc}
        <ImageViewer
          imageSrc={imageSrc}
          overlay={appState.overlayData}
          showRegions={appState.layers.regions}
          showTextlines={appState.layers.textlines}
          showBaselines={appState.layers.baselines}
          wheelZoomEnabled={appState.viewerWheelZoom}
          onHover={(label, type, ev) => showTip(type, label, ev)}
          onLeave={hideTip}
        />
      {:else}
        <div class="flex flex-1 items-center justify-center text-sm text-muted-foreground">
          Select a document from the list.
        </div>
      {/if}
    </section>
  </main>
</div>

<TooltipHud visible={tip.visible} x={tip.x} y={tip.y} title={tip.title} body={tip.body} />
