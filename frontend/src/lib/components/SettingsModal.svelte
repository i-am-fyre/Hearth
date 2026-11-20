<script lang="ts">
  import { api } from "#lib/api.ts";
  import { session } from "#lib/session.svelte.ts";
  import { CURRENCIES, preferences } from "#lib/preferences.svelte.ts";
  import { confirmDialog, dialogState } from "#lib/ui/dialog.svelte.ts";
  import { errorMessage, notify } from "#lib/ui/notify.svelte.ts";

  let {
    open = $bindable(false),
    /** Called with the number of invitations waiting for the signed-in user. */
    oninvitations = (_count: number) => {},
  } = $props();

  const ROLE_LABELS: Record<string, string> = { owner: "Owner", member: "Member", read_only: "Read-Only" };

  let household = $state<any>(null);
  let invitations = $state<any[]>([]);
  let loadingHousehold = $state(false);
  let inviteEmail = $state("");
  let inviteRole = $state("member");
  let isInviting = $state(false);
  let busy = $state(false);

  const members = $derived<any[]>(household?.members ?? []);
  const me = $derived(members.find((m) => m.user_id != null && m.user_id === session.user?.id));
  const isOwner = $derived(me?.role === "owner");
  const ownerCount = $derived(members.filter((m) => m.status !== "pending" && m.role === "owner").length);
  const activeCount = $derived(members.filter((m) => m.status !== "pending").length);
  // The last owner has to make someone else an owner before leaving.
  const canLeave = $derived(!!me && activeCount > 1 && !(isOwner && ownerCount <= 1));

  // Load fresh data each time the window opens.
  $effect(() => {
    if (open) load();
  });

  async function load() {
    loadingHousehold = true;
    try {
      [household, invitations] = await Promise.all([
        api.get("/households/"),
        api.get("/households/invitations"),
      ]);
      oninvitations(invitations.length);
    } catch (e) {
      notify.error(`Couldn't load your household: ${errorMessage(e)}`);
    } finally {
      loadingHousehold = false;
    }
  }

  /** Household membership changes which accounts are visible, so reload the page. */
  function reloadSoon() {
    setTimeout(() => window.location.reload(), 1200);
  }

  async function handleInviteMember() {
    if (!inviteEmail) return;
    isInviting = true;
    const email = inviteEmail;
    try {
      const res = await api.post("/households/invite", { email, role: inviteRole });
      if (res?.status === "role_updated") {
        notify.success(`${email} is now ${ROLE_LABELS[inviteRole] ?? inviteRole}.`);
      } else {
        notify.info(`Invitation sent to ${email}. They'll join once they accept it in Settings.`);
      }
      inviteEmail = "";
      await load();
    } catch (e) {
      notify.error(`Failed to invite member: ${errorMessage(e)}`);
    } finally {
      isInviting = false;
    }
  }

  async function handleRemoveMember(member: any) {
    const ok = await confirmDialog({
      title: "Remove Member",
      message: `Remove ${member.email} from the household? You'll no longer see each other's accounts.`,
      confirmText: "Remove",
      danger: true,
    });
    if (!ok) return;
    busy = true;
    try {
      await api.delete(`/households/member/${member.user_id}`);
      notify.success(`${member.email} was removed from the household.`);
      reloadSoon();
    } catch (e) {
      notify.error(`Failed to remove member: ${errorMessage(e)}`);
      busy = false;
    }
  }

  async function handleLeave() {
    const ok = await confirmDialog({
      title: "Leave Household?",
      message: `You'll stop seeing ${household?.name ?? "this household"}'s shared accounts, and they'll stop seeing yours.`,
      confirmText: "Leave",
      danger: true,
    });
    if (!ok || !me) return;
    busy = true;
    try {
      await api.delete(`/households/member/${me.user_id}`);
      notify.success("You left the household.");
      reloadSoon();
    } catch (e) {
      notify.error(`Couldn't leave the household: ${errorMessage(e)}`);
      busy = false;
    }
  }

  async function handleCancelInvitation(member: any) {
    try {
      await api.delete(`/households/invitations/${member.id}`);
      notify.success(`Cancelled the invitation for ${member.email}.`);
      await load();
    } catch (e) {
      notify.error(`Couldn't cancel the invitation: ${errorMessage(e)}`);
    }
  }

  async function handleAccept(inv: any) {
    const ok = await confirmDialog({
      title: inv.owner_email ? `Join ${inv.owner_email}'s household?` : `Join ${inv.household_name}?`,
      message: "Members of a household can see and edit each other's accounts and transactions.",
      confirmText: "Join",
    });
    if (!ok) return;
    busy = true;
    try {
      await api.post(`/households/invitations/${inv.id}/accept`, {});
      notify.success(`You joined ${inv.household_name}.`);
      reloadSoon();
    } catch (e) {
      notify.error(`Couldn't accept the invitation: ${errorMessage(e)}`);
      busy = false;
    }
  }

  async function handleDecline(inv: any) {
    try {
      await api.delete(`/households/invitations/${inv.id}`);
      notify.info(`Declined the invitation from ${inv.household_name}.`);
      await load();
    } catch (e) {
      notify.error(`Couldn't decline the invitation: ${errorMessage(e)}`);
    }
  }

  function close() {
    open = false;
  }

  function onKeydown(e: KeyboardEvent) {
    // Let an open confirm dialog handle Escape first.
    if (open && e.key === "Escape" && !dialogState.current) close();
  }
</script>

<svelte:window onkeydown={onKeydown} />

{#if open}
  <div
    class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto"
    role="presentation"
    onclick={(e) => { if (e.target === e.currentTarget) close(); }}
  >
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="settings-title"
      class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-md shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200 text-slate-100"
    >
      <div class="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
        <h3 id="settings-title" class="text-xl font-bold">Settings</h3>
        <button
          onclick={close}
          aria-label="Close"
          class="p-2 hover:bg-slate-800 rounded-xl transition-colors text-slate-400"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="p-8 space-y-6">
        {#if invitations.length}
          <section class="space-y-2" aria-labelledby="invites-title">
            <h4 id="invites-title" class="text-sm font-bold text-amber-400">Invitations for you</h4>
            {#each invitations as inv (inv.id)}
              <div class="bg-amber-500/5 border border-amber-500/20 rounded-xl px-4 py-3">
                <p class="text-sm text-slate-200">
                  {#if inv.owner_email}
                    <b>{inv.owner_email}</b> invited you to join their household
                  {:else}
                    You're invited to join <b>{inv.household_name}</b>
                  {/if}
                  as {ROLE_LABELS[inv.role] ?? inv.role}.
                </p>
                <div class="flex gap-2 mt-2">
                  <button
                    onclick={() => handleAccept(inv)}
                    disabled={busy}
                    class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-xs font-bold"
                  >
                    Accept
                  </button>
                  <button
                    onclick={() => handleDecline(inv)}
                    disabled={busy}
                    class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 rounded-lg text-xs font-bold"
                  >
                    Decline
                  </button>
                </div>
              </div>
            {/each}
          </section>
        {/if}

        <div class={invitations.length ? "pt-6 border-t border-slate-800" : ""}>
          <label for="default-currency" class="block text-xs font-bold text-slate-500 uppercase mb-2">
            Default Currency
          </label>
          <select
            id="default-currency"
            bind:value={preferences.defaultCurrency}
            class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-blue-500 transition-colors"
          >
            {#each CURRENCIES as c}
              <option value={c.code}>{c.label}</option>
            {/each}
          </select>
          <p class="text-[10px] text-slate-600 mt-2 italic">
            New accounts will default to this selection. Saved in this browser only.
          </p>
        </div>

        <div class="pt-6 border-t border-slate-800">
          <h4 class="text-sm font-bold text-blue-400 mb-4">{household?.name || "Your Household"}</h4>
          {#if loadingHousehold && !household}
            <p class="text-xs text-slate-500 mb-6">Loading members…</p>
          {:else if members.length}
            <div class="space-y-2 mb-6">
              {#each members as member (member.status + ":" + member.id)}
                {@const isMe = member === me}
                <div class="flex justify-between items-center bg-slate-950 px-4 py-2 rounded-xl border border-slate-800">
                  <div>
                    <span class="text-slate-300 text-sm block">
                      {member.email}
                      {#if isMe}<span class="text-[10px] text-slate-500">(you)</span>{/if}
                    </span>
                    <div class="flex items-center gap-2">
                      <span class="text-[10px] text-slate-500 uppercase tracking-widest">{ROLE_LABELS[member.role] ?? member.role}</span>
                      {#if member.status === "pending"}
                        <span class="text-[8px] bg-amber-500/10 text-amber-500 px-1.5 py-0.5 rounded-full font-black uppercase tracking-widest border border-amber-500/20">Invited</span>
                      {/if}
                    </div>
                  </div>
                  {#if member.status === "pending" && isOwner}
                    <button
                      onclick={() => handleCancelInvitation(member)}
                      aria-label="Cancel invitation for {member.email}"
                      title="Cancel invitation"
                      class="text-slate-400 hover:text-rose-400 p-1 bg-slate-800 rounded"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  {:else if member.status !== "pending" && !isMe && isOwner}
                    <button
                      onclick={() => handleRemoveMember(member)}
                      disabled={busy}
                      aria-label="Remove {member.email}"
                      title="Remove from household"
                      class="text-rose-500 hover:text-rose-400 p-1 bg-rose-500/10 rounded disabled:opacity-50"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  {/if}
                </div>
              {/each}
            </div>
          {/if}

          {#if isOwner}
            <form onsubmit={(e) => { e.preventDefault(); handleInviteMember(); }} class="flex flex-col gap-3">
              <label for="invite-email" class="block text-xs font-bold text-slate-500 uppercase">Invite Member by Email</label>
              <div class="flex flex-col sm:flex-row gap-2">
                <input
                  id="invite-email"
                  type="email"
                  bind:value={inviteEmail}
                  required
                  disabled={isInviting}
                  placeholder="partner@email.com"
                  class="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500"
                />
                <select
                  bind:value={inviteRole}
                  disabled={isInviting}
                  aria-label="Role"
                  class="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500"
                >
                  <option value="owner">Owner</option>
                  <option value="member">Member</option>
                  <option value="read_only">Read-Only</option>
                </select>
                <button
                  type="submit"
                  disabled={isInviting}
                  class="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-sm font-bold transition-all whitespace-nowrap"
                >
                  {isInviting ? "Sending..." : "Invite"}
                </button>
              </div>
              <p class="text-[10px] text-slate-600 italic">
                People join only after accepting. Members can view and change the household's
                data; read-only members can view it but change only their own. Inviting an
                existing member changes their role.
              </p>
            </form>
          {:else if me}
            <p class="text-xs text-slate-500">Only the household owner can invite or remove members.</p>
          {/if}

          {#if canLeave}
            <button
              onclick={handleLeave}
              disabled={busy}
              class="mt-4 text-xs font-bold text-rose-400 hover:text-rose-300 disabled:opacity-50"
            >
              Leave household
            </button>
          {/if}
        </div>
      </div>

      <div class="p-8 bg-slate-900 border-t border-slate-800">
        <button
          onclick={close}
          class="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl shadow-lg shadow-blue-500/20 transition-all"
        >
          Done
        </button>
      </div>
    </div>
  </div>
{/if}
