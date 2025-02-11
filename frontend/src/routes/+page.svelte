<script lang="ts">
  import * as wg from "$lib/wireguard";
  import Configuration from "./Configuration.svelte";
  import DeleteModal from "./DeleteModal.svelte";

  let configurations = $state(wg.fetchConfigurations());
  let selectedConfiguration: number | undefined = $state();

  let isDeleteModalOpen = $state(false);
</script>

<svelte:head>
  <title>WireGuard Manager</title>
</svelte:head>

<header class="flex items-center justify-between py-4 lg:py-6">
  <h1 class="text-2xl font-semibold lg:text-4xl">WireGuard Manager</h1>
  <button>Logout</button>
</header>

<main class="rounded-2xl bg-white shadow-xl">
  <section class="flex items-center justify-between p-4 lg:p-6">
    <h1 class="text-2xl font-bold">Configurations</h1>
    <button>New</button>
  </section>
  <hr class="border-t border-gray-200" />
  <section class="p-4 lg:p-6">
    {#await configurations}
      <p class="text-lg">Loading...</p>
    {:then configurations}
      {#if configurations?.length}
        <ul class="flex flex-col gap-y-2">
          {#each configurations as { id, name, ip }}
            <Configuration
              {name}
              {ip}
              onDeleteClick={() => {
                selectedConfiguration = id;
                isDeleteModalOpen = true;
              }}
            />
          {/each}
        </ul>
      {:else}
        <p>No configurations</p>
      {/if}
    {/await}
  </section>
</main>

<DeleteModal
  bind:isOpen={isDeleteModalOpen}
  onConfirm={async () => {
    await wg.deleteConfiguration(selectedConfiguration!);
    configurations = wg.fetchConfigurations();
  }}
/>
