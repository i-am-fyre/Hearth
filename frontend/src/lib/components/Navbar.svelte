<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/state";
  import { session } from "#lib/session.svelte.ts";
  import { api } from "#lib/api.ts";
  import SettingsModal from "#lib/components/SettingsModal.svelte";

  let showSettings = $state(false);
  let systemInfo = $state<any>(null);
  let invitationCount = $state(0);

  const links = [
    { href: "/", label: "Dashboard" },
    { href: "/accounts", label: "Accounts" },
    { href: "/tags", label: "Tags" },
  ];

  onMount(async () => {
    // Invitations from other households wait in Settings; flag them on the gear.
    api.get("/households/invitations").then((r) => (invitationCount = r?.length ?? 0)).catch(() => {});
    try {
      systemInfo = await api.get("/system/info");
    } catch (e) {
      console.error("Failed to fetch system info", e);
    }
  });

  function handleLogout() {
    session.logout();
  }
</script>

<nav class="bg-slate-900 border-b border-slate-800 p-4 sticky top-0 z-10 backdrop-blur-md bg-opacity-80">
  <div class="max-w-6xl mx-auto flex justify-between items-center">
    <div class="flex items-center gap-3">
      <a href="/" class="text-xl font-bold text-blue-400 hover:text-blue-300 transition-colors">
        Hearth
      </a>
      {#if systemInfo?.update_available}
        <a 
          href="https://github.com/i-am-fyre/Hearth/releases/latest" 
            target="_blank"
            class="px-2 py-0.5 bg-blue-500/10 border border-blue-500/30 text-blue-400 text-[8px] font-black uppercase tracking-widest rounded-full hover:bg-blue-500/20 transition-all flex items-center gap-1 animate-pulse"
          >
            Update Available
            <svg xmlns="http://www.w3.org/2000/svg" class="h-2 w-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        {/if}
    </div>

    <div class="flex items-center gap-6">
      {#if session.user}
        <div class="hidden sm:flex flex-col items-end">
          <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Signed in as</span>
          <span class="text-sm font-medium text-slate-300">{session.user.email}</span>
        </div>
      {/if}
      <div class="flex items-center gap-4">
        {#if session.user}
          <button
            onclick={() => (showSettings = true)}
            class="relative text-slate-400 hover:text-white transition-colors"
            aria-label="Settings"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 0 0 -1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 0 0 -2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 0 0 -2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 0 0 -1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 0 0 1.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              /><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              /></svg
            >
            {#if invitationCount}
              <span class="absolute -top-1 -right-1 h-2.5 w-2.5 rounded-full bg-amber-400 ring-2 ring-slate-900"></span>
              <span class="sr-only">({invitationCount} household invitation{invitationCount === 1 ? '' : 's'} waiting)</span>
            {/if}
          </button>
        {/if}
        {#each links as link}
          {@const active = page.url.pathname === link.href}
          <a
            href={link.href}
            aria-current={active ? "page" : undefined}
            class="text-sm font-medium transition-colors {active ? 'text-white' : 'text-slate-400 hover:text-white'}"
          >
            {link.label}
          </a>
        {/each}
        <button
          onclick={handleLogout}
          class="text-sm font-medium text-slate-400 hover:text-white transition-colors"
        >
          Logout
        </button>
      </div>
    </div>
  </div>
</nav>

<SettingsModal bind:open={showSettings} oninvitations={(n: number) => (invitationCount = n)} />
