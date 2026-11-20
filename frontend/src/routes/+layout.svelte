<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/state';
  import { session } from '#lib/session.svelte.ts';
  import { isPublicPath } from '#lib/routes.ts';
  import Toaster from '#lib/components/Toaster.svelte';
  import DialogHost from '#lib/components/DialogHost.svelte';
  import '../app.css';

  let { children } = $props();

  const isPublic = $derived(isPublicPath(page.url.pathname));

  onMount(() => {
    session.init();
  });

  // Every page except login/register/setup needs a signed-in user.
  $effect(() => {
    if (!isPublic && !session.loading && !session.user) {
      goto('/login');
    }
  });
</script>

<div class="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans">
  <main class="flex-grow">
    {#if isPublic || session.user}
      {@render children()}
    {:else}
      <div class="flex justify-center items-center py-32" aria-label="Loading">
        <div class="w-10 h-10 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
      </div>
    {/if}
  </main>

  <footer class="p-4 text-center text-sm text-slate-500 border-t border-slate-900">
    <p>&copy; {new Date().getFullYear()} Hearth &middot; Personal Finance for Your Household</p>
  </footer>
</div>

<Toaster />
<DialogHost />
