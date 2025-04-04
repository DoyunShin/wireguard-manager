<script lang="ts">
  import FileSaver from "file-saver";
  import { goto } from "$app/navigation";
  import Button from "$lib/Button.svelte";
  import * as wg from "$lib/wireguard";
  import Configuration from "./Configuration.svelte";
  import DeleteModal from "./DeleteModal.svelte";
  import NewModal from "./NewModal.svelte";
  import QrCodeModal from "./QrCodeModal.svelte";

  import IconLogout from "~icons/material-symbols/logout";
  import IconAdd from "~icons/material-symbols/add";

  let configurations = $state(wg.fetchConfigurations());
  let selectedConfiguration: wg.Configuration | undefined = $state();
  let selectedBlob: Blob | undefined = $state();

  let isNewModalOpen = $state(false);
  let isQrCodeModalOpen = $state(false);
  let isDeleteModalOpen = $state(false);

  const refreshConfigurations = async () => {
    configurations = Promise.resolve(await wg.fetchConfigurations());
  };
</script>

<svelte:head>
  <title>WireGuard Manager</title>
</svelte:head>

<header class="flex items-center justify-between py-4 lg:py-6">
  <h1 class="text-2xl font-semibold lg:text-4xl">WireGuard Manager</h1>
  <Button
    color="gray"
    onclick={() => goto("/api/auth/logout")}
    class="flex items-center gap-x-1.5 text-sm lg:text-base"
  >
    <IconLogout />
    <span>Logout</span>
  </Button>
</header>

<main class="rounded-2xl bg-white shadow-xl">
  <section class="flex items-center justify-between p-4 lg:p-6">
    <h1 class="text-2xl font-bold">Configurations</h1>
    <Button
      color="gray"
      onclick={() => (isNewModalOpen = true)}
      class="flex items-center gap-x-1.5 text-sm lg:text-base"
    >
      <IconAdd />
      <span>New</span>
    </Button>
  </section>
  <hr class="border-t border-gray-200" />
  <section class="p-4 lg:p-6">
    {#await configurations.then(async (res) => {
      if (res) return res;
      else await goto("/api/auth/google");
    })}
      <p>Loading...</p>
    {:then configurations}
      {#if configurations?.length}
        <ul class="flex flex-col gap-y-2">
          {#each configurations as configuration}
            <Configuration
              name={configuration.name}
              ip={configuration.ip}
              onQrCodeClick={async () => {
                selectedBlob = undefined;
                isQrCodeModalOpen = true;

                const res = await wg.downloadConfiguration(configuration);
                if (res) {
                  selectedBlob = res.blob;
                }
              }}
              onDownloadClick={async () => {
                const res = await wg.downloadConfiguration(configuration);
                if (res) {
                  FileSaver.saveAs(res.blob, res.filename);
                }
              }}
              onDeleteClick={() => {
                selectedConfiguration = configuration;
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

<NewModal
  bind:isOpen={isNewModalOpen}
  onConfirm={async (name) => {
    await wg.createConfiguration(name);
    await refreshConfigurations();
  }}
/>
<QrCodeModal bind:isOpen={isQrCodeModalOpen} blob={selectedBlob} />
<DeleteModal
  bind:isOpen={isDeleteModalOpen}
  name={selectedConfiguration?.name}
  onConfirm={async () => {
    await wg.deleteConfiguration(selectedConfiguration!.id);
    await refreshConfigurations();
  }}
/>
