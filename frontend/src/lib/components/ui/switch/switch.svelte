<script lang="ts">
  import { cn } from '$lib/utils';

  let {
    checked = $bindable(false),
    'aria-label': ariaLabel = 'Toggle',
    class: className = '',
  }: {
    checked?: boolean;
    'aria-label'?: string;
    class?: string;
  } = $props();
</script>

<button
  type="button"
  role="switch"
  aria-checked={checked}
  aria-label={ariaLabel}
  class={cn(
    'relative h-8 w-[3.25rem] shrink-0 rounded-full border border-white/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
    checked ? 'bg-primary/80' : 'bg-muted',
    className,
  )}
  onclick={() => (checked = !checked)}
>
  <span
    class={cn(
      'pointer-events-none absolute top-1 h-6 w-6 rounded-full bg-card shadow transition-[left] duration-200 ease-out',
      checked ? 'left-[calc(100%-1.625rem)]' : 'left-1',
    )}
  ></span>
</button>
