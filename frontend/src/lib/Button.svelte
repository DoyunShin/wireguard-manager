<script lang="ts">
  import type { Snippet } from "svelte";
  import type { ClassValue } from "svelte/elements";

  interface Props {
    children?: Snippet;
    class?: ClassValue;
    color?: "red" | "blue" | "gray";
    onclick?: () => void;
  }

  let { children, class: className, color = "blue", onclick }: Props = $props();

  let bgColor = $derived(
    {
      red: "bg-red-500 hover:bg-red-600 active:bg-red-600",
      blue: "bg-blue-500 hover:bg-blue-600 active:bg-blue-600",
      gray: "bg-gray-100 hover:bg-gray-200 active:bg-gray-200"
    }[color]
  );
  let textColor = $derived(
    {
      red: "text-white",
      blue: "text-white",
      gray: "text-gray-600"
    }[color]
  );
</script>

<button
  onclick={onclick && (() => setTimeout(onclick, 100))}
  class={[
    "rounded-xl px-4 py-2 font-medium transition duration-100 active:scale-95",
    bgColor,
    textColor,
    className
  ]}
>
  {@render children?.()}
</button>
