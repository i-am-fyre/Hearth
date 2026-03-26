<script lang="ts">
  import { api } from "$lib/api";

  let { 
    accounts = [], 
    isOpen = $bindable(false),
    onimported = () => {},
    onclose = () => {}
  } = $props();

  let step = $state<'upload' | 'map' | 'review'>('upload');
  let file = $state<File | null>(null);
  let previewRows = $state<string[][]>([]);
  let isProcessing = $state(false);

  // Mapping Configuration
  let hasHeader = $state(true);
  let dateCol = $state(0);
  let descCol = $state(1);
  let amountMode = $state<'single' | 'split'>('single');
  let amountCol = $state(2);
  let debitCol = $state(2);
  let creditCol = $state(3);

  let results = $state<any[]>([]);
  let sourceAccountId = $state<number | null>(null);
  let recons = $state<Record<number, number>>({}); // bank_txn_id -> target_acc_id

  // New Account state for inline creation
  let showInlineAddAccount = $state(false);
  let inlineAccountName = $state("");
  let inlineAccountType = $state("expense");
  let targetRuleTxnId = $state<number | null>(null);

  // Selection state for bulk actions
  let selectedIds = $state(new Set<number>());
  let bulkAccountId = $state<number | null>(null);
  let filterText = $state("");

  // Custom Confirm Modal State
  let confirmState = $state<{
    show: boolean;
    title: string;
    message: string;
    confirmText: string;
    isDanger: boolean;
    onConfirm: () => void;
  }>({
    show: false,
    title: "",
    message: "",
    confirmText: "Confirm",
    isDanger: false,
    onConfirm: () => {}
  });

  function showConfirm(options: { title: string, message: string, confirmText?: string, isDanger?: boolean, onConfirm: () => void }) {
    confirmState = {
      show: true,
      title: options.title,
      message: options.message,
      confirmText: options.confirmText || "Confirm",
      isDanger: options.isDanger || false,
      onConfirm: options.onConfirm
    };
  }

  let filteredResults = $derived(
    results.filter(item => {
      if (!filterText) return true;
      const search = filterText.toLowerCase();
      return item.description.toLowerCase().includes(search) || 
             item.amount.toString().includes(search);
    })
  );

  let allUnmatchedSelected = $derived(
    filteredResults.length > 0 && 
    filteredResults.filter(item => item.status !== 'matched').every(item => selectedIds.has(item.id))
  );
  
  function toggleSelectAll() {
    if (allUnmatchedSelected) {
      filteredResults.forEach(_t => {
        if (_t.status !== 'matched') selectedIds.delete(_t.id);
      });
    } else {
      filteredResults.forEach(_t => {
        if (_t.status !== 'matched') selectedIds.add(_t.id);
      });
    }
    selectedIds = new Set(selectedIds);
  }

  function toggleSelect(id: number) {
    if (selectedIds.has(id)) {
      selectedIds.delete(id);
    } else {
      selectedIds.add(id);
    }
    selectedIds = new Set(selectedIds);
  }

  function bulkAssign() {
    if (!bulkAccountId) return;
    selectedIds.forEach(id => {
      recons[id] = bulkAccountId!;
    });
    selectedIds = new Set();
    bulkAccountId = null;
  }

  async function performBulkDiscard() {
    isProcessing = true;
    try {
      for (const id of Array.from(selectedIds)) {
        console.log(`Deleting import ${id}`);
        await api.delete(`/imports/${id}`);
      }
      results = results.filter(_t => !selectedIds.has(_t.id));
      selectedIds = new Set();
      if (results.length === 0) step = 'upload';
      console.log("bulkDiscard success");
      onimported();
    } catch (e: any) {
      console.error("bulkDiscard error", e);
      alert(`Failed to discard some transactions: ${e.message}`);
    } finally {
      isProcessing = false;
    }
  }

  function bulkDiscard() {
    const count = selectedIds.size;
    showConfirm({
      title: `Discard ${count} Transactions?`,
      message: `Are you sure you want to discard these ${count} selected transactions? They will be removed from your feed.`,
      confirmText: "Discard",
      isDanger: true,
      onConfirm: () => {
        confirmState.show = false;
        performBulkDiscard();
      }
    });
  }

  async function createQuickRule(txn: any) {
    const targetAccountId = recons[txn.id];
    if (!targetAccountId) {
      alert("Please select a category for this transaction first so we know where to assign it.");
      return;
    }

    const merchant = prompt("Enter merchant name or keyword for this rule:", txn.description);
    if (!merchant) return;

    const autoPost = confirm(`Should we automatically post transactions matching "${merchant}" to the ledger in the future? (Bypasses manual review)`);

    isProcessing = true;
    try {
      await api.post("/rules/", {
        priority: 10,
        condition_json: { merchant_contains: merchant },
        action_json: { assign_account_id: targetAccountId },
        active: true,
        auto_post: autoPost
      });
      alert(`Rule created! ${autoPost ? 'Auto-posting is enabled.' : 'Future matches will be suggested automatically.'}`);
      
      // Update other transactions in the current feed that match
      results.forEach(_t => {
        if (_t.status !== 'matched' && !recons[_t.id] && _t.description.toLowerCase().includes(merchant.toLowerCase())) {
          recons[_t.id] = targetAccountId;
        }
      });
    } catch (e: any) {
      alert(`Failed to create rule: ${e.message}`);
    } finally {
      isProcessing = false;
    }
  }

  async function handleFileSelect(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;
    
    file = input.files[0];
    isProcessing = true;
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await api.postForm("/imports/preview", formData);
      previewRows = response.preview;
      step = 'map';
      
      // Try to guess amount mode based on column count
      if (previewRows.length > 0 && previewRows[0].length >= 4) {
        amountMode = 'split';
      }
    } catch (e: any) {
      alert(`Failed to preview CSV: ${e.message}`);
    } finally {
      isProcessing = false;
    }
  }

  async function processImport() {
    if (!file) return;
    isProcessing = true;
    
    const config = {
      has_header: hasHeader,
      date_col: dateCol,
      desc_col: descCol,
      amount_col: amountMode === 'single' ? amountCol : null,
      debit_col: amountMode === 'split' ? debitCol : null,
      credit_col: amountMode === 'split' ? creditCol : null
    };

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("config", JSON.stringify({
        ...config,
        source_account_id: sourceAccountId
      }));
      
      results = await api.postForm("/imports/csv", formData);
      
      // Initialize recons from suggestions
      results.forEach(_t => {
        if (_t.suggested_account_id) {
          recons[_t.id] = _t.suggested_account_id;
        }
      });
      
      step = 'review';
    } catch (e: any) {
      alert(`Import failed: ${e.message}`);
    } finally {
      isProcessing = false;
    }
  }

  async function postToLedger() {
    if (!sourceAccountId) {
      alert("Please select the bank account where these funds came from.");
      return;
    }

    isProcessing = true;
    let count = 0;
    try {
      for (const txn of results) {
        if (txn.status === 'matched') continue; // Already exists
        
        const targetId = recons[txn.id];
        if (!targetId) continue; // Skip if no account selected
        
        await api.post("/imports/reconcile", {
          bank_txn_id: txn.id,
          source_account_id: sourceAccountId,
          target_account_id: targetId
        });
        count++;
      }
      alert(`Successfully posted ${count} transactions to ledger.`);
      finish();
    } catch (e: any) {
      alert(`Failed to post: ${e.message}`);
    } finally {
      isProcessing = false;
    }
  }

  async function handleInlineAccountSubmit() {
    if (!inlineAccountName) return;
    isProcessing = true;
    try {
      const acc = await api.post("/accounts/", {
        name: inlineAccountName,
        type: inlineAccountType,
        currency: "CAD"
      });
      // Update recons and accounts list
      if (targetRuleTxnId !== null) {
        recons[targetRuleTxnId] = acc.id;
      }
      accounts = [...accounts, acc];
      showInlineAddAccount = false;
      inlineAccountName = "";
    } catch (e: any) {
      alert(`Failed to create account: ${e.message}`);
    } finally {
      isProcessing = false;
    }
  }

  async function performDiscardTransaction(txnId: number) {
    isProcessing = true;
    try {
      await api.delete(`/imports/${txnId}`);
      results = results.filter(_t => _t.id !== txnId);
      if (results.length === 0) {
        step = 'upload';
      }
      onimported();
    } catch (e: any) {
      alert(`Failed to discard: ${e.message}`);
    } finally {
      isProcessing = false;
    }
  }

  function discardTransaction(txnId: number) {
    showConfirm({
      title: "Discard Transaction?",
      message: "Are you sure you want to discard this bank transaction? It will be removed from your feed.",
      confirmText: "Discard",
      isDanger: true,
      onConfirm: () => {
        confirmState.show = false;
        performDiscardTransaction(txnId);
      }
    });
  }

  async function performDiscardAllTransactions() {
    isProcessing = true;
    try {
      console.log("Calling bulk delete API...");
      await api.delete("/imports/bulk");
      results = [];
      step = 'upload';
      console.log("discardAllTransactions success");
      onimported();
    } catch (e: any) {
      console.error("discardAllTransactions error", e);
      alert(`Failed to discard all: ${e.message}`);
    } finally {
      isProcessing = false;
    }
  }

  function discardAllTransactions() {
    showConfirm({
      title: "Discard All Unreconciled?",
      message: "Are you sure you want to discard ALL unreconciled bank transactions? This cannot be undone.",
      confirmText: "Discard All",
      isDanger: true,
      onConfirm: () => {
        confirmState.show = false;
        performDiscardAllTransactions();
      }
    });
  }

  // Fetch existing unmatched on open if not already in a flow
  $effect(() => {
    if (isOpen && step === 'upload') {
      isProcessing = true;
      api.get("/imports/unmatched").then(data => {
        if (data && data.length > 0) {
          results = data;
          // Initialize recons from suggestions
          results.forEach(_t => {
            if (_t.suggested_account_id) {
              recons[_t.id] = _t.suggested_account_id;
            }
          });
          step = 'review';
        }
      }).finally(() => {
          isProcessing = false;
      });
    }
  });

  function close() {
    file = null;
    previewRows = [];
    results = [];
    step = 'upload';
    isOpen = false;
    onclose();
  }

  function finish() {
    onimported();
    close();
  }
</script>

{#if isOpen}
  <div class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[70] flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
      <header class="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
        <div>
          <h3 class="text-xl font-bold text-blue-400">Bank Import Center</h3>
          <p class="text-xs text-slate-500 mt-1 uppercase tracking-widest font-bold">
            {#if step === 'upload'}Step 1: Upload Statement{:else if step === 'map'}Step 2: Map Columns{:else}Step 3: Review Results{/if}
          </p>
        </div>
        <button onclick={close} class="p-2 hover:bg-slate-800 rounded-xl transition-colors text-slate-400">
           <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </header>

      <div class="flex-1 overflow-y-auto p-10 custom-scrollbar relative">
        {#if isProcessing && step === 'upload'}
            <div class="absolute inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex flex-col items-center justify-center space-y-4">
                <div class="w-16 h-16 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
                <p class="text-blue-400 font-bold uppercase tracking-widest text-xs">Syncing Bank Feed...</p>
            </div>
        {/if}

        {#if step === 'upload'}
          <div class="flex flex-col items-center justify-center py-20 border-2 border-dashed border-slate-800 rounded-3xl hover:border-blue-500/50 transition-all bg-slate-950/50">
            <div class="w-20 h-20 bg-blue-500/10 rounded-full flex items-center justify-center mb-6">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h4 class="text-lg font-bold text-slate-300">Drop your bank CSV here</h4>
            <p class="text-sm text-slate-500 mb-8">Supports statement formats from most major banks</p>
            
            <label class="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl cursor-pointer shadow-lg shadow-blue-900/20 transition-all">
              {isProcessing ? "Reading..." : "Select File"}
              <input type="file" class="hidden" accept=".csv" onchange={handleFileSelect} disabled={isProcessing} />
            </label>
          </div>
        {:else if step === 'map'}
          <div class="space-y-8">
            <div class="bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden">
               <div class="p-4 border-b border-slate-800 bg-slate-900/30 flex justify-between items-center">
                <span class="text-xs font-bold text-slate-400 uppercase tracking-widest">CSV Preview</span>
                <label class="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" bind:checked={hasHeader} class="w-4 h-4 rounded border-slate-700 bg-slate-900 text-blue-500 focus:ring-0" />
                    <span class="text-xs font-bold text-slate-500 uppercase tracking-widest">First row is header</span>
                </label>
               </div>
               <div class="overflow-x-auto">
                 <table class="w-full text-left text-xs">
                   <thead>
                     <tr class="bg-slate-900/50">
                       {#if previewRows.length > 0}
                         {#each previewRows[0] as _, i}
                           <th class="p-3 border-r border-slate-800 text-slate-500 font-mono">Col {i}</th>
                         {/each}
                       {/if}
                     </tr>
                   </thead>
                   <tbody class="divide-y divide-slate-800">
                     {#each previewRows as row}
                       <tr class="hover:bg-slate-900/30">
                         {#each row as cell}
                           <td class="p-3 border-r border-slate-800 text-slate-300 truncate max-w-[200px]">{cell}</td>
                         {/each}
                       </tr>
                     {/each}
                   </tbody>
                 </table>
               </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-8 bg-slate-900/30 p-6 rounded-2xl border border-slate-800">
               <div class="space-y-4">
                  <h4 class="text-sm font-bold text-blue-400 uppercase tracking-widest">Field Mapping</h4>
                  
                  <div class="space-y-2">
                    <label for="dateCol" class="text-[10px] font-bold text-slate-500 uppercase mb-1 block">Date Column</label>
                    <select id="dateCol" bind:value={dateCol} class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm outline-none focus:border-blue-500">
                        {#each (previewRows[0] || []) as _, i}
                          <option value={i}>Column {i} : {previewRows[0][i] || 'Empty'}</option>
                        {/each}
                    </select>
                  </div>

                  <div class="space-y-2">
                    <label for="descCol" class="text-[10px] font-bold text-slate-500 uppercase mb-1 block">Description Column</label>
                    <select id="descCol" bind:value={descCol} class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm outline-none focus:border-blue-500">
                        {#each (previewRows[0] || []) as _, i}
                          <option value={i}>Column {i} : {previewRows[0][i] || 'Empty'}</option>
                        {/each}
                    </select>
                  </div>
               </div>

               <div class="space-y-4">
                  <div class="flex justify-between items-center">
                    <h4 class="text-sm font-bold text-blue-400 uppercase tracking-widest">Amount Mapping</h4>
                    <div class="flex bg-slate-950 rounded-lg p-1 border border-slate-800">
                        <button 
                          onclick={() => amountMode = 'single'}
                          class="px-3 py-1 text-[10px] font-bold rounded-md transition-all {amountMode === 'single' ? 'bg-blue-600 text-white' : 'text-slate-500'}">Single</button>
                        <button 
                          onclick={() => amountMode = 'split'}
                          class="px-3 py-1 text-[10px] font-bold rounded-md transition-all {amountMode === 'split' ? 'bg-blue-600 text-white' : 'text-slate-500'}">Split</button>
                    </div>
                  </div>

                  {#if amountMode === 'single'}
                    <div class="space-y-2">
                        <label for="amountCol" class="text-[10px] font-bold text-slate-500 uppercase mb-1 block">Amount Column (Net)</label>
                        <select id="amountCol" bind:value={amountCol} class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm outline-none focus:border-blue-500">
                            {#each (previewRows[0] || []) as _, i}
                            <option value={i}>Column {i} : {previewRows[0][i] || 'Empty'}</option>
                            {/each}
                        </select>
                    </div>
                  {:else}
                    <div class="grid grid-cols-2 gap-4">
                        <div class="space-y-2">
                            <label for="debitCol" class="text-[10px] font-bold text-slate-500 uppercase mb-1 block">Spending (Debit)</label>
                            <select id="debitCol" bind:value={debitCol} class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm outline-none focus:border-blue-500">
                                {#each (previewRows[0] || []) as _, i}
                                <option value={i}>Column {i} : {previewRows[0][i] || 'Empty'}</option>
                                {/each}
                            </select>
                        </div>
                        <div class="space-y-2">
                            <label for="creditCol" class="text-[10px] font-bold text-slate-500 uppercase mb-1 block">Payments (Credit)</label>
                            <select id="creditCol" bind:value={creditCol} class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm outline-none focus:border-blue-500">
                                {#each (previewRows[0] || []) as _, i}
                                <option value={i}>Column {i} : {previewRows[0][i] || 'Empty'}</option>
                                {/each}
                            </select>
                        </div>
                    </div>
                  {/if}
               </div>
            </div>
          </div>
        {:else if step === 'review'}
          <div class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="flex items-center gap-4 bg-emerald-500/10 border border-emerald-500/20 p-6 rounded-2xl">
                  <div class="w-12 h-12 bg-emerald-500/20 rounded-full flex items-center justify-center text-emerald-400">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                  </div>
                  <div>
                      <h4 class="text-lg font-bold text-emerald-400">Analysis Complete</h4>
                      <p class="text-sm text-slate-400">Found {results.length} transactions.</p>
                  </div>
              </div>

              <div class="bg-blue-500/10 border border-blue-500/20 p-6 rounded-2xl">
                <label class="text-[10px] font-bold text-blue-400 uppercase mb-2 block tracking-widest">Statement Account (Source)</label>
                <select 
                  bind:value={sourceAccountId}
                  class="w-full bg-slate-950 border border-blue-500/30 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-blue-500 text-slate-200">
                  <option value={null}>-- Select Account --</option>
                  {#each accounts as acc}
                    <option value={acc.id}>{acc.name} ({acc.type})</option>
                  {/each}
                </select>
                <p class="text-[9px] text-slate-500 mt-2 italic">Transactions will be credited/debited against this account.</p>
              </div>
            </div>

            <div class="bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden">
                <div class="p-4 border-b border-slate-800 bg-slate-900/30 flex flex-wrap justify-between items-center gap-4">
                    <div class="flex flex-wrap items-center gap-3">
                        <span class="text-xs font-bold text-slate-400 uppercase tracking-widest">Reconciliation Review</span>
                        <div class="hidden sm:block h-4 w-px bg-slate-800"></div>
                        <div class="relative">
                           <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                             <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                           </svg>
                           <input 
                              type="text" 
                              bind:value={filterText}
                              placeholder="Search description or amount..."
                              class="bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1 text-[10px] w-48 outline-none focus:border-blue-500/50 text-slate-300 transition-all"
                           />
                        </div>
                        <button 
                            onclick={discardAllTransactions}
                            class="text-[9px] bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 font-bold uppercase px-2 py-1 rounded-md transition-all border border-rose-500/10 whitespace-nowrap"
                        >
                            Discard All Unreconciled
                        </button>
                    </div>

                    {#if selectedIds.size > 0}
                      <div class="flex flex-wrap items-center gap-3 bg-blue-500/10 border border-blue-500/20 px-3 py-1.5 rounded-xl animate-in fade-in slide-in-from-right-4 ml-auto">
                        <span class="text-[10px] font-black text-blue-400 uppercase tracking-widest whitespace-nowrap">{selectedIds.size} Selected</span>
                        <div class="hidden sm:block h-4 w-px bg-blue-500/20"></div>
                        <div class="flex items-center gap-2">
                           <select 
                             bind:value={bulkAccountId}
                             class="bg-slate-950 border border-blue-500/30 rounded-lg px-2 py-1 text-[10px] outline-none focus:border-blue-500 text-slate-300">
                             <option value={null}>-- Bulk Assign --</option>
                             {#each accounts as acc}
                               <option value={acc.id}>{acc.name}</option>
                             {/each}
                           </select>
                           <button 
                             onclick={bulkAssign}
                             disabled={!bulkAccountId}
                             class="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold rounded-lg disabled:opacity-50 transition-all">
                             Apply
                           </button>
                        </div>
                        <div class="hidden sm:block h-4 w-px bg-blue-500/20"></div>
                        <button 
                          onclick={bulkDiscard}
                          class="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white text-[10px] font-bold rounded-lg transition-all">
                          Discard
                        </button>
                      </div>
                    {:else}
                      <span class="text-[10px] text-slate-500 font-bold uppercase ml-auto">Categorize to post to ledger</span>
                    {/if}
                </div>
                <div class="max-h-[400px] overflow-y-auto">
                    <table class="w-full text-left text-xs">
                        <thead class="sticky top-0 bg-slate-900/90 z-10">
                            <tr class="text-slate-500 border-b border-slate-800 font-bold uppercase tracking-tighter">
                                <th class="p-3 w-10">
                                   <input 
                                     type="checkbox" 
                                     checked={allUnmatchedSelected}
                                     onchange={toggleSelectAll}
                                     class="w-4 h-4 rounded border-slate-700 bg-slate-900 text-blue-500 focus:ring-0" 
                                   />
                                </th>
                                <th class="p-3">Date</th>
                                <th class="p-3">Description</th>
                                <th class="p-3">Amount</th>
                                <th class="p-3">Category (Target)</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-800">
                            {#each filteredResults as txn}
                                <tr class="hover:bg-slate-900/30 transition-colors {txn.status === 'matched' ? 'opacity-50 grayscale' : ''}">
                                    <td class="p-3">
                                       {#if txn.status !== 'matched'}
                                         <input 
                                           type="checkbox" 
                                           checked={selectedIds.has(txn.id)}
                                           onchange={() => toggleSelect(txn.id)}
                                           class="w-4 h-4 rounded border-slate-700 bg-slate-900 text-blue-500 focus:ring-0" 
                                         />
                                       {/if}
                                    </td>
                                    <td class="p-3 text-slate-400">{txn.date}</td>
                                    <td class="p-3">
                                      <div class="text-slate-200 font-medium truncate max-w-[200px]" title={txn.description}>{txn.description}</div>
                                      {#if txn.status === 'matched'}
                                        <div class="text-[9px] text-emerald-400 font-bold uppercase mt-1 flex items-center gap-1">
                                          <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                                          </svg>
                                          Existing Match
                                        </div>
                                      {:else if txn.suggested_account_name}
                                        <div class="text-[9px] text-blue-400 font-bold uppercase mt-1 flex items-center gap-1">
                                          <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                                            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                                          </svg>
                                          Suggested: {txn.suggested_account_name}
                                        </div>
                                      {/if}
                                    </td>
                                    <td class="p-3 font-mono {Number(txn.amount) < 0 ? 'text-rose-400' : 'text-emerald-400'}">
                                        {Number(txn.amount).toFixed(2)}
                                    </td>
                                    <td class="p-3">
                                        {#if txn.status !== 'matched'}
                                          <div class="flex flex-col gap-2">
                                            <div class="flex gap-2">
                                                <select 
                                                  value={recons[txn.id] || ""}
                                                  onchange={(e) => { 
                                                    recons[txn.id] = Number(e.currentTarget.value);
                                                  }}
                                                  class="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-2 py-1.5 text-[11px] outline-none focus:border-blue-500 text-slate-300">
                                                  <option value="">-- Assign Category --</option>
                                                  {#each accounts as acc}
                                                    <option value={acc.id}>{acc.name}</option>
                                                  {/each}
                                                </select>
                                                <button 
                                                  onclick={() => createQuickRule(txn)}
                                                  class="p-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded-lg transition-colors"
                                                  title="Create Automation Rule"
                                                >
                                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                                                    </svg>
                                                </button>
                                                <button 
                                                  onclick={() => discardTransaction(txn.id)}
                                                  class="p-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded-lg transition-colors"
                                                  title="Discard Transaction"
                                                >
                                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                    </svg>
                                                </button>
                                            </div>
                                            <button 
                                              onclick={() => { targetRuleTxnId = txn.id; showInlineAddAccount = true; }}
                                              class="text-left text-[9px] text-slate-500 hover:text-blue-400 font-bold uppercase flex items-center gap-1 pl-1">
                                              <svg xmlns="http://www.w3.org/2000/svg" class="h-2.5 w-2.5" viewBox="0 0 20 20" fill="currentColor">
                                                <path fill-rule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clip-rule="evenodd" />
                                              </svg>
                                              New Category
                                            </button>
                                          </div>
                                        {:else}
                                          <span class="text-slate-600 italic">Matched</span>
                                        {/if}
                                    </td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            </div>
          </div>
        {/if}
      </div>

      <footer class="p-6 border-t border-slate-800 flex justify-end gap-3 bg-slate-900/50 text-xs">
        <button onclick={close} class="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-xl transition-all">
          Cancel
        </button>
        
        {#if step === 'map'}
          <button 
            onclick={processImport} 
            disabled={isProcessing}
            class="px-8 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl shadow-lg shadow-blue-900/20 transition-all flex items-center gap-2">
            {#if isProcessing}
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
            {:else}
                Run Import Analysis
            {/if}
          </button>
        {:else if step === 'review'}
          <button 
            onclick={postToLedger}
            disabled={isProcessing || !sourceAccountId}
            class="px-8 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-900/20 transition-all disabled:opacity-50 disabled:grayscale">
            Post to Ledger
          </button>
        {/if}
      </footer>
    </div>
  </div>
{/if}

{#if showInlineAddAccount}
  <div class="fixed inset-0 bg-black/60 backdrop-blur-md z-[80] flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-md shadow-2xl p-8 space-y-6">
      <h4 class="text-xl font-bold text-blue-400">Quick Create Category</h4>
      <div class="space-y-4">
        <div>
          <label class="text-[10px] font-bold text-slate-500 uppercase mb-1 block">Account Name</label>
          <input 
            type="text" 
            bind:value={inlineAccountName}
            placeholder="e.g. Starbucks, Rent, Salary"
            class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm outline-none focus:border-blue-500 text-slate-200"
          />
        </div>
        <div>
          <label class="text-[10px] font-bold text-slate-500 uppercase mb-1 block">Account Type</label>
          <select 
            bind:value={inlineAccountType}
            class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm outline-none focus:border-blue-500 text-slate-200">
            <option value="expense">Expense</option>
            <option value="income">Income</option>
            <option value="asset">Asset (Transfer)</option>
            <option value="liability">Liability</option>
          </select>
        </div>
      </div>
      <div class="flex gap-3 justify-end pt-4">
        <button onclick={() => showInlineAddAccount = false} class="px-6 py-2 text-slate-400 font-bold uppercase text-xs">Cancel</button>
        <button 
          onclick={handleInlineAccountSubmit}
          disabled={!inlineAccountName || isProcessing}
          class="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl text-xs">Create & Assign</button>
      </div>
    </div>
  </div>
{/if}

{#if confirmState.show}
  <div class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[90] flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-sm shadow-2xl p-8 space-y-6">
      <header class="text-center">
        {#if confirmState.isDanger}
          <div class="w-16 h-16 bg-rose-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
          </div>
        {:else}
          <div class="w-16 h-16 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
          </div>
        {/if}
        <h3 class="text-2xl font-bold text-white">{confirmState.title}</h3>
        <p class="text-sm text-slate-400 mt-2">{confirmState.message}</p>
      </header>

      <footer class="flex flex-col gap-3 pt-4">
        <button 
          onclick={confirmState.onConfirm}
          class="w-full px-6 py-3 {confirmState.isDanger ? 'bg-rose-600 hover:bg-rose-500 shadow-rose-900/20' : 'bg-blue-600 hover:bg-blue-500 shadow-blue-900/20'} text-white font-bold rounded-2xl shadow-lg transition-all"
        >
          {confirmState.confirmText}
        </button>
        <button 
          onclick={() => confirmState.show = false}
          class="w-full px-6 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-2xl transition-all"
        >
          Cancel
        </button>
      </footer>
    </div>
  </div>
{/if}

<style>
    .custom-scrollbar::-webkit-scrollbar {
        width: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
        background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 10px;
    }
    table {
        border-collapse: collapse;
    }
</style>
