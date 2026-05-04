<script lang="ts">
  import { cn } from '$lib/utils';
  import type { Snippet } from 'svelte';
  import type { HTMLButtonAttributes } from 'svelte/elements';

  type Variant = 'default' | 'outline' | 'ghost';

  let {
    class: className = '',
    variant = 'default' as Variant,
    type = 'button' as const,
    children,
    ...rest
  }: HTMLButtonAttributes & { variant?: Variant; children?: Snippet } = $props();

  const base =
    'inline-flex items-center justify-center gap-1 rounded-md text-[11px] font-medium uppercase tracking-[0.08em] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:pointer-events-none disabled:opacity-50';
  const variants: Record<Variant, string> = {
    default: 'bg-primary/90 text-primary-foreground hover:bg-primary',
    outline: 'border border-white/10 bg-card hover:bg-muted',
    ghost: 'hover:bg-muted',
  };
</script>

<button type={type} class={cn(base, variants[variant], 'px-3 py-1.5', className)} {...rest}>
  {@render children?.()}
</button>
