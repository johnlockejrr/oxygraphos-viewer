<script lang="ts">
  import type { OverlayData } from '$lib/api/client';

  let {
    data,
    showRegions,
    showTextlines,
    showBaselines,
    onHover,
    onLeave,
  }: {
    data: OverlayData | null;
    showRegions: boolean;
    showTextlines: boolean;
    showBaselines: boolean;
    onHover: (label: string, type: string, ev: MouseEvent) => void;
    onLeave: () => void;
  } = $props();

  function pointsStr(coords: { x: number; y: number }[]) {
    return coords.map((p) => `${p.x},${p.y}`).join(' ');
  }

  function regionClass(type: string) {
    const t = type.replace(/Region$/, '').toLowerCase();
    return `overlay-region overlay-region--${t}`;
  }
</script>

{#if data}
  <svg
    viewBox="0 0 1 1"
    class="pointer-events-none absolute inset-0 h-full w-full"
    preserveAspectRatio="none"
    role="presentation"
    onmouseleave={onLeave}
  >
    {#if showRegions}
      <g class="layer-regions pointer-events-auto">
        {#each data.regions as region (region.id)}
          <polygon
            class={regionClass(region.type)}
            points={pointsStr(region.coords)}
            role="graphics-symbol"
            aria-label={region.label || region.id}
            onmousemove={(e) => onHover(region.label || region.id, region.type, e)}
          />
        {/each}
      </g>
    {/if}

    {#if showTextlines}
      <g class="layer-textlines pointer-events-auto">
        {#each data.regions as region (region.id)}
          {#each region.textlines as line (line.id)}
            <polygon
              class="overlay-textline"
              points={pointsStr(line.coords)}
              role="graphics-symbol"
              aria-label={line.label || line.id}
              onmousemove={(e) => onHover(line.label || line.id, 'TextLine', e)}
            />
          {/each}
        {/each}
      </g>
    {/if}

    {#if showBaselines}
      <g class="layer-baselines pointer-events-auto">
        {#each data.regions as region (region.id)}
          {#each region.textlines as line (line.id)}
            {#if line.baseline}
              <polyline
                class="overlay-baseline"
                points={pointsStr(line.baseline.points)}
                fill="none"
                role="graphics-symbol"
                aria-label={line.baseline.id}
                onmousemove={(e) => onHover(line.baseline?.id || line.id, 'Baseline', e)}
              />
            {/if}
          {/each}
        {/each}
      </g>
    {/if}
  </svg>
{/if}
