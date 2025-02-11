<script lang="ts">
  import "../app.css";
  let { children } = $props();
</script>

<div class="min-h-screen min-w-sm bg-gray-100">
  <div class="mx-auto max-w-screen-xl px-4">
    {@render children()}
  </div>
</div>
