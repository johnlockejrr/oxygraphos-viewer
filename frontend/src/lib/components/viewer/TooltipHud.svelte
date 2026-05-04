<script lang="ts">
  let {
    visible = false,
    x = 0,
    y = 0,
    title = '',
    body = '',
  }: {
    visible?: boolean;
    x?: number;
    y?: number;
    title?: string;
    body?: string;
  } = $props();
</script>

<div
  class="pointer-events-none fixed z-50 max-w-sm rounded-md border border-white/10 bg-card px-3 py-2 text-xs shadow-lg transition-opacity duration-100"
  class:opacity-0={!visible}
  class:opacity-100={visible}
  style:left="{x + 12}px; top:{y + 12}px;"
  role="tooltip"
  aria-live="polite"
>
  <div class="mb-0.5 text-[10px] font-medium uppercase tracking-wider text-primary">{title}</div>
  <div class="break-all font-mono text-[11px] text-foreground">{body}</div>
</div>
