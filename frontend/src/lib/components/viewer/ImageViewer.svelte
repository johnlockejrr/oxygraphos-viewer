<script lang="ts">
  import type { OverlayData } from '$lib/api/client';
  import { Button } from '$lib/components/ui/button';
  import OverlayLayer from './OverlayLayer.svelte';

  let {
    imageSrc,
    overlay,
    showRegions,
    showTextlines,
    showBaselines,
    wheelZoomEnabled = false,
    onHover,
    onLeave,
  }: {
    imageSrc: string;
    overlay: OverlayData | null;
    showRegions: boolean;
    showTextlines: boolean;
    showBaselines: boolean;
    wheelZoomEnabled?: boolean;
    onHover: (label: string, type: string, ev: MouseEvent) => void;
    onLeave: () => void;
  } = $props();

  /** Zoom multiplier on top of “fit to panel” (1 = fitted like before). */
  let zoom = $state(1);
  let naturalW = $state(0);
  let naturalH = $state(0);
  let scrollEl: HTMLDivElement | undefined = $state();
  /** Viewport size inside the scroll container (for object-contain fit). */
  let viewW = $state(0);
  let viewH = $state(0);
  const zoomRef = { v: 1 };

  /** Tracks prior `wheelZoomEnabled` so we only reset when turning wheel zoom off. */
  let prevWheelZoom: boolean | undefined = undefined;

  $effect(() => {
    zoomRef.v = zoom;
  });

  $effect(() => {
    const w = wheelZoomEnabled;
    if (prevWheelZoom === true && w === false) {
      zoom = 1;
      zoomRef.v = 1;
      queueMicrotask(() => {
        scrollEl?.scrollTo({ left: 0, top: 0, behavior: 'instant' });
      });
    }
    prevWheelZoom = w;
  });

  $effect(() => {
    imageSrc;
    zoom = 1;
    zoomRef.v = 1;
    naturalW = 0;
    naturalH = 0;
  });

  $effect(() => {
    void wheelZoomEnabled;
    const el = scrollEl;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      if (!wheelZoomEnabled) return;
      e.preventDefault();
      const z = zoomRef.v;
      const factor = e.deltaY > 0 ? 0.92 : 1.08;
      const nz = Math.min(6, Math.max(0.15, z * factor));
      zoomRef.v = nz;
      zoom = nz;
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  });

  $effect(() => {
    const el = scrollEl;
    if (!el || typeof ResizeObserver === 'undefined') return;
    const pad = 8;
    const apply = () => {
      viewW = Math.max(1, el.clientWidth - pad);
      viewH = Math.max(1, el.clientHeight - pad);
    };
    apply();
    const ro = new ResizeObserver(apply);
    ro.observe(el);
    return () => ro.disconnect();
  });

  /** Scale so the full image fits in the scroll viewport (max 1 = never upscale). */
  const fitScale = $derived.by(() => {
    if (naturalW <= 0 || naturalH <= 0 || viewW <= 0 || viewH <= 0) return 1;
    return Math.min(1, viewW / naturalW, viewH / naturalH);
  });

  const renderW = $derived.by(() =>
    naturalW > 0 ? Math.max(1, naturalW * fitScale * zoom) : 0,
  );
  const renderH = $derived.by(() =>
    naturalH > 0 ? Math.max(1, naturalH * fitScale * zoom) : 0,
  );

  function onImgLoad(e: Event) {
    const t = e.currentTarget as HTMLImageElement;
    naturalW = t.naturalWidth;
    naturalH = t.naturalHeight;
  }
</script>

<div class="flex min-h-0 flex-1 flex-col gap-2">
  <div class="flex flex-wrap items-center gap-2">
    <span class="text-[10px] font-mono text-muted-foreground">
      {#if wheelZoomEnabled}
        Scroll wheel: zoom · scrollbars to pan
      {:else}
        Wheel zoom off — enable below to zoom with the mouse wheel
      {/if}
    </span>
    <span class="text-[10px] font-mono tabular-nums text-primary">{Math.round(zoom * 100)}%</span>
    <span class="text-[10px] text-muted-foreground">(100% = fit to panel)</span>
    {#if zoom !== 1}
      <Button
        variant="outline"
        type="button"
        class="!px-2 !py-1 text-[10px]"
        onclick={() => {
          zoom = 1;
          zoomRef.v = 1;
        }}
      >
        Reset zoom
      </Button>
    {/if}
  </div>

  <div
    bind:this={scrollEl}
    class="max-h-[85vh] min-h-[200px] max-w-full flex-1 overflow-auto rounded-md border border-white/10 bg-black/35"
  >
    {#key imageSrc}
      <div
        class="relative inline-block p-1"
        style:width="{renderW > 0 ? `${renderW}px` : undefined}"
        style:height="{renderH > 0 ? `${renderH}px` : undefined}"
      >
        <img
          src={imageSrc}
          alt="Document scan"
          class="block bg-black/40"
          style:width="{renderW > 0 ? `${renderW}px` : undefined}"
          style:height="{renderH > 0 ? `${renderH}px` : undefined}"
          draggable="false"
          onload={onImgLoad}
        />
        {#if naturalW > 0 && renderW > 0}
          <OverlayLayer
            data={overlay}
            {showRegions}
            {showTextlines}
            {showBaselines}
            {onHover}
            {onLeave}
          />
        {/if}
      </div>
    {/key}
  </div>
</div>
