<script lang="ts">
  import * as wg from "$lib/wireguard";
  import Configuration from "./Configuration.svelte";

  let configurations = $state(wg.fetchConfigurations());
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
        <ul class="space-y-2">
          {#each configurations as { name, ip }}
            <Configuration {name} {ip} />
          {/each}
        </ul>
      {:else}
        <p>No configurations</p>
      {/if}
    {/await}
  </section>
</main>
