<script lang="ts">
  import type { ClassValue } from "svelte/elements";

  interface Props {
    class?: ClassValue;
    oninput?: (value: string) => void;
    placeholder: string;
    value?: string;
  }

  let { class: className, oninput, placeholder, value = $bindable("") }: Props = $props();
</script>

<div class={className}>
  <div class="relative mt-5">
    <input
      bind:value
      type="text"
      placeholder=""
      oninput={oninput && (() => oninput(value))}
      class="w-full border-b-2 border-gray-300 py-1 text-xl transition duration-300 ease-in-out outline-none"
    />
    <!-- svelte-ignore a11y_label_has_associated_control -->
    <label
      class="pointer-events-none absolute top-1/2 left-0 -translate-y-1/2 transform text-xl text-gray-400 transition-all duration-300 ease-in-out"
    >
      {placeholder}
    </label>
  </div>
</div>

<style>
  @reference "../app.css";

  input:focus,
  input:not(:placeholder-shown) {
    @apply border-blue-300;
  }
  input:focus + label,
  input:not(:placeholder-shown) + label {
    @apply top-0 -translate-y-full text-sm text-blue-400;
  }
</style>
