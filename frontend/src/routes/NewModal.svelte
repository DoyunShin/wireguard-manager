<script lang="ts">
  import Button from "$lib/Button.svelte";
  import Modal from "$lib/Modal.svelte";
  import TextInput from "$lib/TextInput.svelte";

  interface Props {
    isOpen: boolean;
    onConfirm: (name: string) => void;
  }

  let { isOpen = $bindable(), onConfirm }: Props = $props();

  let value = $state("");
  let isEmptyName = $state(false);

  $effect.pre(() => {
    if (isOpen) {
      value = "";
      isEmptyName = false;
    }
  });
</script>

<Modal bind:isOpen class="space-y-4 p-4">
  <div class="flex flex-col gap-y-2">
    <h1 class="text-xl font-bold">New Configuration</h1>
    <TextInput
      bind:value
      placeholder="Name"
      oninput={(value) => (isEmptyName = value.trim().length === 0)}
    />
    {#if isEmptyName}
      <p class="text-sm font-semibold text-red-400">Name required.</p>
    {/if}
  </div>
  <div class="flex justify-end gap-x-2">
    <Button color="gray" onclick={() => (isOpen = false)}>Cancel</Button>
    <Button
      color="blue"
      onclick={() => {
        const valueTrimmed = value.trim();
        if (!valueTrimmed) {
          isEmptyName = true;
          return;
        }

        onConfirm(valueTrimmed);
        isOpen = false;
      }}
    >
      Create
    </Button>
  </div>
</Modal>
