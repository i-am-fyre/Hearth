<script lang="ts">
  import { notify, type ToastKind } from "#lib/ui/notify.svelte.ts";

  const styles: Record<ToastKind, { bar: string; icon: string; label: string }> = {
    success: { bar: "bg-emerald-500", icon: "text-emerald-400", label: "Success" },
    error: { bar: "bg-rose-500", icon: "text-rose-400", label: "Error" },
    info: { bar: "bg-blue-500", icon: "text-blue-400", label: "Notice" },
  };
</script>

<div
  class="fixed bottom-4 right-4 left-4 sm:left-auto z-[110] flex flex-col gap-2 sm:w-96 pointer-events-none"
>
  {#each notify.toasts as toast (toast.id)}
    <div
      role={toast.kind === "error" ? "alert" : "status"}
      aria-live={toast.kind === "error" ? "assertive" : "polite"}
      class="pointer-events-auto relative overflow-hidden flex items-start gap-3 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl pl-5 pr-3 py-3 animate-in slide-in-from-bottom-2 fade-in duration-200"
    >
      <span class="absolute left-0 top-0 bottom-0 w-1 {styles[toast.kind].bar}"></span>
      <div class="flex-1 min-w-0">
        <p class="text-[10px] font-black uppercase tracking-widest {styles[toast.kind].icon}">
          {styles[toast.kind].label}
        </p>
        <p class="text-sm text-slate-200 mt-0.5 break-words">{toast.message}</p>
      </div>
      <button
        onclick={() => notify.dismiss(toast.id)}
        aria-label="Dismiss notification"
        class="p-1 text-slate-500 hover:text-white transition-colors rounded-lg"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  {/each}
</div>
