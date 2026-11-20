<script lang="ts">
  import { tick } from "svelte";
  import { dialogState } from "#lib/ui/dialog.svelte.ts";

  let input = $state<HTMLInputElement | null>(null);
  let confirmButton = $state<HTMLButtonElement | null>(null);

  // Focus the text field (prompt) or the confirm button (confirm) when a dialog opens.
  $effect(() => {
    const dialog = dialogState.current;
    if (!dialog) return;
    tick().then(() => {
      if (dialog.kind === "prompt") input?.select();
      else confirmButton?.focus();
    });
  });

  function onKeydown(e: KeyboardEvent) {
    if (dialogState.current && e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      dialogState.close(false);
    }
  }
</script>

<svelte:window onkeydown={onKeydown} />

{#if dialogState.current}
  {@const dialog = dialogState.current}
  <div
    class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
    role="presentation"
    onclick={(e) => { if (e.target === e.currentTarget) dialogState.close(false); }}
  >
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="hearth-dialog-title"
      class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-sm shadow-2xl p-6 text-center animate-in zoom-in-95 duration-200"
    >
    <form onsubmit={(e) => { e.preventDefault(); dialogState.close(true); }}>
      <h3 id="hearth-dialog-title" class="text-xl font-bold mb-2 text-white">{dialog.title}</h3>
      {#if dialog.message}
        <p class="text-slate-400 mb-6 text-sm whitespace-pre-line">{dialog.message}</p>
      {/if}
      {#if dialog.kind === "prompt"}
        <input
          bind:this={input}
          bind:value={dialog.value}
          placeholder={dialog.placeholder}
          aria-label={dialog.title}
          class="w-full mb-6 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm outline-none focus:border-blue-500 text-white"
        />
      {/if}
      <div class="flex gap-3">
        <button
          type="button"
          onclick={() => dialogState.close(false)}
          class="flex-1 py-3 px-4 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-xl transition-colors"
        >
          {dialog.cancelText ?? "Cancel"}
        </button>
        <button
          bind:this={confirmButton}
          type="submit"
          disabled={dialog.kind === "prompt" && !dialog.value.trim()}
          class="flex-1 py-3 px-4 {dialog.danger
            ? 'bg-rose-600 hover:bg-rose-500'
            : 'bg-blue-600 hover:bg-blue-500'} disabled:opacity-50 text-white font-bold rounded-xl transition-colors"
        >
          {dialog.confirmText ?? (dialog.kind === "prompt" ? "OK" : "Confirm")}
        </button>
      </div>
    </form>
    </div>
  </div>
{/if}
