<script lang="ts">
  import type { Snippet } from "svelte";
  import type { ClassValue } from "svelte/elements";
  import { fade } from "svelte/transition";

  interface Props {
    children: Snippet;
    class?: ClassValue;
    isOpen: boolean;
  }

  let { children, class: className, isOpen = $bindable() }: Props = $props();
</script>

{#if isOpen}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    onclick={() => (isOpen = false)}
    class="fixed inset-0 z-10 flex items-center justify-center bg-black/50"
    transition:fade={{ duration: 100 }}
  >
    <div class="w-fit max-w-screen-xl min-w-sm p-4">
      <div onclick={(e) => e.stopPropagation()} class={["rounded-2xl bg-white", className]}>
        {@render children()}
      </div>
    </div>
  </div>
{/if}
