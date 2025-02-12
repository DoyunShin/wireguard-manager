<script lang="ts">
  import QRCode from "qrcode";
  import Modal from "$lib/Modal.svelte";

  import IconClose from "~icons/material-symbols/close";

  interface Props {
    isOpen: boolean;
    blob?: Blob;
  }

  let { isOpen = $bindable(), blob }: Props = $props();
</script>

<Modal bind:isOpen class="space-y-4 p-4">
  <div class="flex items-center justify-between">
    <h1 class="text-xl font-bold">QR code</h1>
    <button
      onclick={() => (isOpen = false)}
      class="text-xl text-gray-600 hover:text-gray-800 active:text-gray-800"
    >
      <IconClose />
    </button>
  </div>
  <div class="flex justify-center">
    {#if blob}
      {#await blob.text().then((text) => QRCode.toDataURL(text, { margin: 2, width: 320 }))}
        <p>Loading...</p>
      {:then qrcode}
        <img src={qrcode} alt="QR Code" />
      {/await}
    {:else}
      <p>Loading...</p>
    {/if}
  </div>
</Modal>
