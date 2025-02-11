<script lang="ts">
  interface Props {
    name: string;
    ip: string;
  }

  let { name, ip }: Props = $props();
</script>

<li class="flex items-center justify-between gap-x-2 p-2">
  <div class="flex-grow space-y-1 overflow-x-hidden">
    <h2 class="truncate text-lg font-medium">{name}</h2>
    <p class="truncate text-gray-400">{ip}</p>
  </div>
  <div class="flex-shrink-0 space-x-2">
    <button>QR code</button>
    <button>Download</button>
    <button>Delete</button>
  </div>
</li>
