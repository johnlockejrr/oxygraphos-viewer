<script lang="ts">
  import { Button } from '$lib/components/ui/button';

  let {
    page,
    pages,
    onPrev,
    onNext,
  }: {
    page: number;
    pages: number;
    onPrev: () => void;
    onNext: () => void;
  } = $props();
</script>

<div class="flex items-center justify-between gap-2 border-t border-white/10 px-2 py-3">
  <Button variant="outline" type="button" onclick={onPrev} disabled={page <= 1}>Prev</Button>
  <span class="font-mono text-[11px] text-muted-foreground">Page {page} / {pages}</span>
  <Button variant="outline" type="button" onclick={onNext} disabled={page >= pages}>Next</Button>
</div>
