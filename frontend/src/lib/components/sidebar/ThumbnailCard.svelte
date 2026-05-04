<script lang="ts">
  import type { DocumentItem } from '$lib/api/client';
  import { onMount } from 'svelte';

  let {
    doc,
    active,
    onSelect,
  }: {
    doc: DocumentItem;
    active: boolean;
    onSelect: (id: string) => void;
  } = $props();

  let el: HTMLButtonElement | undefined;
  let visible = $state(false);

  onMount(() => {
    if (!el) return;
    const obs = new IntersectionObserver(
      ([e]) => {
        if (e?.isIntersecting) visible = true;
      },
      { rootMargin: '80px', threshold: 0.01 },
    );
    obs.observe(el);
    return () => obs.disconnect();
  });
</script>

<button
  type="button"
  bind:this={el}
  role="option"
  aria-selected={active}
  class="group flex w-full flex-col gap-1 rounded-md border border-transparent bg-card p-2 text-left transition-all hover:bg-muted/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
  class:shadow-[inset_3px_0_0_theme(colors.primary.DEFAULT)]={active}
  class:bg-muted={active}
  onclick={() => onSelect(doc.id)}
>
  <div class="relative flex aspect-[3/4] w-full items-center justify-center overflow-hidden rounded-sm bg-black/50">
    {#if visible}
      <img src={doc.thumb_url} alt="" class="max-h-40 w-full object-contain" loading="lazy" />
    {:else}
      <div class="h-32 w-full animate-pulse bg-muted"></div>
    {/if}
  </div>
  <div class="truncate px-0.5 font-mono text-[10px] tracking-wide text-muted-foreground group-hover:text-foreground">
    {doc.filename}.xml
  </div>
</button>
