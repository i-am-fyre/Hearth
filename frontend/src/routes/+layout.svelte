<script lang="ts">
  import { onMount } from 'svelte';
  import { session } from '$lib/session.svelte';
  import '../app.css';

  let { children } = $props();

  onMount(() => {
    session.init();
  });
</script>

<div class="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans">
  <main class="flex-grow">
    {@render children()}
  </main>

  <footer class="p-4 text-center text-sm text-slate-500 border-t border-slate-900">
    <p>&copy; 2026 Hearth &middot; Personal Finance for Your Household</p>
  </footer>
</div>
