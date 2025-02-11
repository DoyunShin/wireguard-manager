<script lang="ts">
  import Button from "$lib/Button.svelte";
  import Modal from "$lib/Modal.svelte";

  interface Props {
    isOpen: boolean;
    onConfirm: () => void;
  }

  let { isOpen = $bindable(), onConfirm }: Props = $props();
</script>

<Modal bind:isOpen class="space-y-4 p-4">
  <div class="space-y-2">
    <h1 class="text-xl font-bold">Do you want to delete this?</h1>
    <p>
      The configuration <strong>'{name}'</strong> will be permanently removed, and this action cannot
      be undone.
    </p>
  </div>
  <div class="flex justify-end gap-x-2">
    <Button color="gray" onclick={() => (isOpen = false)}>Cancel</Button>
    <Button
      color="red"
      onclick={() => {
        onConfirm();
        isOpen = false;
      }}
    >
      Delete
    </Button>
  </div>
</Modal>
