<script lang="ts">
  import { onMount } from "svelte";
  import { api } from "$lib/api";
  import Navbar from "$lib/components/Navbar.svelte";

  interface Account {
    id: number;
    name: string;
    type: string;
    currency: string;
    balance: number;
  }

  let accounts = $state<Account[]>([]);
  let loading = $state(true);
  let showAddAccount = $state(false);
  let showEditAccount = $state(false);
  let showDeleteConfirm = $state(false);
  let editingAccount = $state<Account | null>(null);
  let accountToDelete = $state<Account | null>(null);

  // Form state
  let newAccountName = $state("");
  let newAccountType = $state("expense");
  let editAccountName = $state("");
  let editAccountType = $state("");

  onMount(async () => {
    await fetchAccounts();
  });

  async function fetchAccounts() {
    loading = true;
    try {
      accounts = await api.get("/accounts/");
    } catch (e: any) {
      alert(`Failed to load accounts: ${e.message}`);
    } finally {
      loading = false;
    }
  }

  async function handleCreateAccount() {
    if (!newAccountName) return;
    try {
      await api.post("/accounts/", {
        name: newAccountName,
        type: newAccountType,
        currency: "CAD"
      });
      newAccountName = "";
      showAddAccount = false;
      await fetchAccounts();
    } catch (e: any) {
      alert(`Failed to create account: ${e.message}`);
    }
  }

  async function handleUpdateAccount() {
    console.log("handleUpdateAccount called", { editingAccount, editAccountName, editAccountType });
    if (!editingAccount || !editAccountName) {
        console.warn("Update skipped: missing editingAccount or editAccountName");
        return;
    }
    try {
      await api.put(`/accounts/${editingAccount.id}`, {
        name: editAccountName,
        type: editAccountType
      });
      showEditAccount = false;
      editingAccount = null;
      await fetchAccounts();
    } catch (e: any) {
      console.error("Update failed", e);
      alert(`Failed to update account: ${e.message}`);
    }
  }

  async function handleDeleteAccount() {
    if (!accountToDelete) return;
    try {
      await api.delete(`/accounts/${accountToDelete.id}`);
      showDeleteConfirm = false;
      accountToDelete = null;
      await fetchAccounts();
    } catch (e: any) {
      alert(`Failed to delete account: ${e.message}`);
    }
  }

  function openEdit(account: Account) {
    editingAccount = account;
    editAccountName = account.name;
    editAccountType = account.type;
    showEditAccount = true;
  }

  function openDelete(account: Account) {
    accountToDelete = account;
    showDeleteConfirm = true;
  }
</script>

<svelte:head>
  <title>Accounts | Hearth</title>
</svelte:head>

<Navbar />

<div class="min-h-screen bg-slate-950 text-slate-200 p-8">
  <div class="max-w-6xl mx-auto space-y-8">
    <header class="flex justify-between items-end">
      <div>
        <h1 class="text-4xl font-black tracking-tighter text-white">Accounts <span class="text-blue-500">.</span></h1>
        <p class="text-slate-500 font-medium uppercase tracking-widest text-[10px] mt-1">Manage your financial structure</p>
      </div>
      <button 
        onclick={() => showAddAccount = true}
        class="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl shadow-lg shadow-blue-900/20 transition-all flex items-center gap-2 text-sm"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clip-rule="evenodd" />
        </svg>
        New Account
      </button>
    </header>

    {#if loading}
      <div class="flex justify-center py-20">
        <div class="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
      </div>
    {:else}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {#each accounts as account (account.id)}
          <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 hover:border-slate-700 transition-all group relative overflow-hidden">
            <div class="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
              <button 
                onclick={() => openEdit(account)}
                class="p-2 bg-slate-800 hover:bg-blue-500/20 text-slate-400 hover:text-blue-400 rounded-xl transition-all"
                title="Edit Account"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </button>
              <button 
                onclick={() => openDelete(account)}
                class="p-2 bg-slate-800 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 rounded-xl transition-all"
                title="Delete Account"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>

            <div class="space-y-4">
              <div>
                <span class="text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/50">
                  {account.type}
                </span>
                <h3 class="text-xl font-bold text-white mt-3 truncate pr-16">{account.name}</h3>
              </div>
              
              <div class="flex items-baseline gap-1">
                <span class="text-3xl font-black tracking-tighter {account.balance < 0 ? 'text-rose-400' : 'text-emerald-400'}">
                  {Math.abs(account.balance).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <span class="text-xs font-bold text-slate-500 uppercase tracking-widest">{account.currency}</span>
              </div>

              <div class="pt-4 border-t border-slate-800/50 flex justify-between items-center">
                <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Available Balance</span>
                <div class="h-1.5 w-1.5 rounded-full {account.balance < 0 ? 'bg-rose-500' : 'bg-emerald-500'} shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
              </div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>

<!-- Add Account Modal -->
{#if showAddAccount}
  <div class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-md shadow-2xl p-8 space-y-6">
      <header>
        <h3 class="text-2xl font-bold text-white">Create Account</h3>
        <p class="text-xs text-slate-500 mt-1 uppercase tracking-widest font-bold">New financial entity</p>
      </header>

      <div class="space-y-4">
        <div class="space-y-2">
          <label for="newAccountName" class="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Account Name</label>
          <input 
            id="newAccountName"
            type="text" 
            bind:value={newAccountName}
            placeholder="e.g. My Savings, Main Checking"
            class="w-full bg-slate-950 border border-slate-800 rounded-2xl px-5 py-4 text-sm outline-none focus:border-blue-500 text-white transition-all shadow-inner"
          />
        </div>

        <div class="space-y-2">
          <label for="newAccountType" class="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Account Type</label>
          <select 
            id="newAccountType"
            bind:value={newAccountType}
            class="w-full bg-slate-950 border border-slate-800 rounded-2xl px-5 py-4 text-sm outline-none focus:border-blue-500 text-white transition-all"
          >
            <option value="asset">Asset (Bank, Cash, Savings)</option>
            <option value="liability">Liability (Credit Card, Loan)</option>
            <option value="expense">Expense (Spending Category)</option>
            <option value="income">Income (Earnings Source)</option>
            <option value="equity">Equity</option>
          </select>
        </div>
      </div>

      <footer class="flex gap-4 pt-4">
        <button 
          onclick={() => showAddAccount = false}
          class="flex-1 px-6 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-2xl transition-all"
        >
          Cancel
        </button>
        <button 
          onclick={handleCreateAccount}
          disabled={!newAccountName}
          class="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl shadow-lg shadow-blue-900/20 transition-all disabled:opacity-50"
        >
          Create
        </button>
      </footer>
    </div>
  </div>
{/if}

<!-- Edit Account Modal -->
{#if showEditAccount}
  <div class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-md shadow-2xl p-8 space-y-6">
      <header>
        <h3 class="text-2xl font-bold text-white">Edit Account</h3>
        <p class="text-xs text-slate-500 mt-1 uppercase tracking-widest font-bold">Update details</p>
      </header>

      <div class="space-y-4">
        <div class="space-y-2">
          <label for="editAccountName" class="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Account Name</label>
          <input 
            id="editAccountName"
            type="text" 
            bind:value={editAccountName}
            class="w-full bg-slate-950 border border-slate-800 rounded-2xl px-5 py-4 text-sm outline-none focus:border-blue-500 text-white transition-all shadow-inner"
          />
        </div>

        <div class="space-y-2">
          <label for="editAccountType" class="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Account Type</label>
          <select 
            id="editAccountType"
            bind:value={editAccountType}
            class="w-full bg-slate-950 border border-slate-800 rounded-2xl px-5 py-4 text-sm outline-none focus:border-blue-500 text-white transition-all"
          >
            <option value="asset">Asset</option>
            <option value="liability">Liability</option>
            <option value="income">Income</option>
            <option value="expense">Expense</option>
            <option value="equity">Equity</option>
          </select>
        </div>
      </div>

      <footer class="flex gap-4 pt-4">
        <button 
          onclick={() => showEditAccount = false}
          class="flex-1 px-6 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-2xl transition-all"
        >
          Cancel
        </button>
        <button 
          onclick={handleUpdateAccount}
          disabled={!editAccountName}
          class="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl shadow-lg shadow-blue-900/20 transition-all disabled:opacity-50"
        >
          Save Changes
        </button>
      </footer>
    </div>
  </div>
{/if}

<!-- Delete Confirmation Modal -->
{#if showDeleteConfirm}
  <div class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-sm shadow-2xl p-8 space-y-6">
      <header class="text-center">
        <div class="w-16 h-16 bg-rose-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
        </div>
        <h3 class="text-2xl font-bold text-white">Delete Account?</h3>
        <p class="text-sm text-slate-400 mt-2">
            Are you sure you want to delete <span class="text-white font-bold">{accountToDelete?.name}</span>? 
            This action can only be performed if there are no transactions.
        </p>
      </header>

      <footer class="flex flex-col gap-3 pt-4">
        <button 
          onclick={handleDeleteAccount}
          class="w-full px-6 py-3 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-2xl shadow-lg shadow-rose-900/20 transition-all"
        >
          Yes, Delete Account
        </button>
        <button 
          onclick={() => { showDeleteConfirm = false; accountToDelete = null; }}
          class="w-full px-6 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-2xl transition-all"
        >
          Cancel
        </button>
      </footer>
    </div>
  </div>
{/if}

<style>
  :global(body) {
    background-color: #020617;
  }
</style>
