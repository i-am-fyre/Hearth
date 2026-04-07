<script lang="ts">
  import { session } from "$lib/session.svelte";

  let { showSettings = $bindable(undefined) } = $props();

  function handleLogout() {
    session.logout();
  }
</script>

<nav class="bg-slate-900 border-b border-slate-800 p-4 sticky top-0 z-10 backdrop-blur-md bg-opacity-80">
  <div class="max-w-6xl mx-auto flex justify-between items-center">
    <a href="/" class="text-xl font-bold text-blue-400 hover:text-blue-300 transition-colors">Hearth</a>
    <div class="flex items-center gap-6">
      {#if session.user}
        <div class="hidden sm:flex flex-col items-end">
          <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Signed in as</span>
          <span class="text-sm font-medium text-slate-300">{session.user.email}</span>
        </div>
      {/if}
      <div class="flex items-center gap-4">
        {#if showSettings !== undefined}
          <button
            onclick={() => (showSettings = true)}
            class="text-slate-400 hover:text-white transition-colors"
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
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 0 0 -1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 0 0 -2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 0 0 -2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 0 0 -1.065-2.572-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 0 0 1.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              /><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              /></svg
            >
          </button>
        {/if}
        <a
          href="/accounts"
          class="text-sm font-medium text-slate-400 hover:text-white transition-colors"
        >
          Accounts
        </a>
        <a
          href="/tags"
          class="text-sm font-medium text-slate-400 hover:text-white transition-colors"
        >
          Tags
        </a>
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
