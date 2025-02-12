<script lang="ts">
  import type { Component } from "svelte";

  import IconQrCode2 from "~icons/material-symbols/qr-code-2";
  import IconDownload from "~icons/material-symbols/download";
  import IconDeleteOutline from "~icons/material-symbols/delete-outline";

  interface Props {
    name: string;
    ip: string;
    onQrCodeClick: () => void;
    onDownloadClick: () => void;
    onDeleteClick: () => void;
  }

  let { name, ip, onQrCodeClick, onDownloadClick, onDeleteClick }: Props = $props();
</script>

<li class="flex items-center justify-between gap-x-2 p-2">
  <div class="flex-grow space-y-1 overflow-x-hidden">
    <h2 class="truncate text-xl font-medium">{name}</h2>
    <p class="truncate text-gray-400">{ip}</p>
  </div>
  <div class="flex flex-shrink-0 gap-x-2">
    {#snippet button(icon: Component, onclick?: () => void)}
      {@const Icon = icon}
      <button
        onclick={onclick && (() => setTimeout(onclick, 100))}
        class="rounded-xl bg-gray-100 p-2 text-lg text-gray-600 transition duration-100 hover:bg-gray-200 active:scale-95 active:bg-gray-200 lg:text-xl"
      >
        <Icon />
      </button>
    {/snippet}

    {@render button(IconQrCode2, onQrCodeClick)}
    {@render button(IconDownload, onDownloadClick)}
    {@render button(IconDeleteOutline, onDeleteClick)}
  </div>
</li>
