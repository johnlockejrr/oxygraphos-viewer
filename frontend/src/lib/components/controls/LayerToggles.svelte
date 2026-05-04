<script lang="ts">
  import Switch from '$lib/components/ui/switch/switch.svelte';

  let {
    layers = $bindable({
      regions: true,
      textlines: true,
      baselines: true,
    }),
  }: {
    layers?: { regions: boolean; textlines: boolean; baselines: boolean };
  } = $props();
</script>

<div class="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:gap-x-8 sm:gap-y-2">
  <label
    class="inline-flex cursor-pointer items-center justify-between gap-4 sm:justify-start sm:gap-3 min-w-0 sm:min-w-[10rem]"
  >
    <span class="shrink-0 text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
      Regions
    </span>
    <Switch bind:checked={layers.regions} aria-label="Toggle regions overlay" class="shrink-0" />
  </label>
  <label
    class="inline-flex cursor-pointer items-center justify-between gap-4 sm:justify-start sm:gap-3 min-w-0 sm:min-w-[10rem]"
  >
    <span class="shrink-0 text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
      Text lines
    </span>
    <Switch bind:checked={layers.textlines} aria-label="Toggle text line overlay" class="shrink-0" />
  </label>
  <label
    class="inline-flex cursor-pointer items-center justify-between gap-4 sm:justify-start sm:gap-3 min-w-0 sm:min-w-[10rem]"
  >
    <span class="shrink-0 text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
      Baselines
    </span>
    <Switch bind:checked={layers.baselines} aria-label="Toggle baseline overlay" class="shrink-0" />
  </label>
</div>
