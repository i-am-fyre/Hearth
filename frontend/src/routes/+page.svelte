<script lang="ts">
  import { onMount } from "svelte";
  import { api, BASE_URL } from "$lib/api";
  import { goto } from "$app/navigation";
  import { session } from "$lib/session.svelte";
  import Navbar from "$lib/components/Navbar.svelte";
  import ImportCenter from "$lib/components/ImportCenter.svelte";
  import {
    Chart as ChartJS,
    Title,
    Tooltip,
    Legend,
    LineElement,
    LinearScale,
    PointElement,
    CategoryScale,
    LineController,
    ArcElement,
    DoughnutController,
    Filler
  } from "chart.js";

  ChartJS.register(
    Title,
    Tooltip,
    Legend,
    LineElement,
    LinearScale,
    PointElement,
    CategoryScale,
    LineController,
    ArcElement,
    DoughnutController,
    Filler
  );

  function chartAction(node: HTMLCanvasElement, config: any) {
    let chart = new ChartJS(node, config);
    return {
      update(newConfig: any) {
        chart.data = newConfig.data;
        chart.options = newConfig.options;
        chart.update("none");
      },
      destroy() {
        chart.destroy();
      },
    };
  }

  interface Entry {
    account_id: number;
    debit: number;
    credit: number;
    description?: string | null;
  }

  interface Transaction {
    id: number;
    date: string;
    description: string;
    entries: Entry[];
    receipt_id?: number | null;
  }

  interface Account {
    id: number;
    name: string;
    type: string;
    currency: string;
    balance: number;
  }

  let transactions = $state<Transaction[]>([]);
  let accounts = $state<Account[]>([]);
  let budgets = $state<any[]>([]);
  let rules = $state<any[]>([]);
  let budgetVariances = $state<Record<number, any>>({});
  let currentTab = $state<'overview' | 'budgets' | 'rules' | 'bank-feed'>('overview');
  let currentUser: any = $state(null);
  let household: any = $state(null);
  let loading = $state(true);
  let isUploading = $state(false);
  let showAddAccount = $state(false);
  let showAddTransaction = $state(false);
  let showVerifyModal = $state(false);
  let showMatchModal = $state(false);
  let verifyExtractionMethod = $state<string>("");
  let potentialMatches = $state<any[]>([]);
  let showSettings = $state<boolean>(false);
  let showTransactionDetail = $state<boolean>(false);
  let isEditingTransaction = $state<boolean>(false);
  let editTransactionData = $state<any>(null);
  let selectedTransaction = $state<Transaction | null>(null);
  
  // Custom Confirm Modal State
  let confirmState = $state({
    show: false,
    title: "",
    message: "",
    onConfirm: () => {},
  });

  function requestConfirm(title: string, message: string, onConfirm: () => void) {
    confirmState = {
      show: true,
      title,
      message,
      onConfirm
    };
  }
  let showImportCenter = $state(false);
  let unreconciledCount = $state<number>(0);
  let isAttachingReceipt = $state<boolean>(false);
  let isUpdatingMatch = $state<boolean>(false);
  let matchTransactionId = $state<number | null>(null);
  let showReceiptCenter = $state<boolean>(false);
  let pendingReceipts = $state<any[]>([]);
  let isBatchUploading = $state<boolean>(false);
  let filterAccountId = $state<number | null>(null);
  let defaultCurrency = $state<string>("USD");
  let dateFilterPreset = $state<string>("this-month");
  let customStartDate = $state("");
  let customEndDate = $state("");
  let pendingReceipt = $state<any>(null);
  let receiptImageUrl = $state<string | null>(null);

  function getDateRange(preset: string) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    let start: Date | null = null;
    let end: Date | null = null;

    switch (preset) {
      case "today":
        start = today;
        end = new Date(today);
        end.setDate(end.getDate() + 1);
        break;
      case "yesterday":
        start = new Date(today);
        start.setDate(start.getDate() - 1);
        end = today;
        break;
      case "this-week": {
        const day = today.getDay(); // 0 is Sunday, 1 is Monday
        const diff = today.getDate() - day + (day === 0 ? -6 : 1);
        start = new Date(today.setDate(diff));
        end = new Date(start);
        end.setDate(end.getDate() + 7);
        break;
      }
      case "last-week": {
        const day = today.getDay();
        const diff = today.getDate() - day + (day === 0 ? -13 : -6);
        start = new Date(today.setDate(diff));
        end = new Date(start);
        end.setDate(end.getDate() + 7);
        break;
      }
      case "this-month":
        start = new Date(now.getFullYear(), now.getMonth(), 1);
        end = new Date(now.getFullYear(), now.getMonth() + 1, 1);
        break;
      case "last-month":
        start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        end = new Date(now.getFullYear(), now.getMonth(), 1);
        break;
      case "this-year":
        start = new Date(now.getFullYear(), 0, 1);
        end = new Date(now.getFullYear() + 1, 0, 1);
        break;
      case "last-year":
        start = new Date(now.getFullYear() - 1, 0, 1);
        end = new Date(now.getFullYear(), 0, 1);
        break;
      case "q1-this":
        start = new Date(now.getFullYear(), 0, 1);
        end = new Date(now.getFullYear(), 3, 1);
        break;
      case "q2-this":
        start = new Date(now.getFullYear(), 3, 1);
        end = new Date(now.getFullYear(), 6, 1);
        break;
      case "q3-this":
        start = new Date(now.getFullYear(), 6, 1);
        end = new Date(now.getFullYear(), 9, 1);
        break;
      case "q4-this":
        start = new Date(now.getFullYear(), 9, 1);
        end = new Date(now.getFullYear() + 1, 0, 1);
        break;
      case "q1-last":
        start = new Date(now.getFullYear() - 1, 0, 1);
        end = new Date(now.getFullYear() - 1, 3, 1);
        break;
      case "q2-last":
        start = new Date(now.getFullYear() - 1, 3, 1);
        end = new Date(now.getFullYear() - 1, 6, 1);
        break;
      case "q3-last":
        start = new Date(now.getFullYear() - 1, 6, 1);
        end = new Date(now.getFullYear() - 1, 9, 1);
        break;
      case "q4-last":
        start = new Date(now.getFullYear() - 1, 9, 1);
        end = new Date(now.getFullYear(), 0, 1);
        break;
      case "last-3y":
        start = new Date(now.getFullYear() - 3, now.getMonth(), now.getDate());
        end = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
        break;
      case "last-7y":
        start = new Date(now.getFullYear() - 7, now.getMonth(), now.getDate());
        end = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
        break;
      case "custom":
        if (customStartDate) start = new Date(customStartDate);
        if (customEndDate) {
          end = new Date(customEndDate);
          end.setDate(end.getDate() + 1);
        }
        break;
    }
    return { start, end };
  }

  let filteredTransactions = $derived.by(() => {
    let result = transactions;

    // Filtering by Account
    if (filterAccountId) {
      result = result.filter((t) =>
        t.entries.some((e) => e.account_id === filterAccountId),
      );
    }

    // Filtering by Date
    const { start, end } = getDateRange(dateFilterPreset);
    if (start || end) {
      result = result.filter((t) => {
        const d = new Date(t.date);
        if (start && d < start) return false;
        if (end && d >= end) return false;
        return true;
      });
    }

    return result;
  });

  let netWorth = $derived(accounts.reduce((acc, a) => {
    if (a.type === "asset") return acc + (Number(a.balance) || 0);
    if (a.type === "liability") return acc - (Number(a.balance) || 0);
    return acc;
  }, 0));

  let assetAccounts = $derived(accounts.filter((a) => a.type === "asset"));
  let liabilityAccounts = $derived(accounts.filter((a) => a.type === "liability"));
  let trackingAccounts = $derived(accounts.filter(
    (a) => a.type === "income" || a.type === "expense" || a.type === "equity",
  ));

  let chartVisibleAccounts = $state<Record<number, boolean>>({});


  let chartData = $derived.by(() => {
    const targetAccounts = accounts.filter(
      (a) =>
        (a.type === "asset" || a.type === "liability") &&
        chartVisibleAccounts[a.id],
    );
    const sortedTxns = [...transactions].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
    );

    const { start, end } = getDateRange(dateFilterPreset);

    let current = start
      ? new Date(start)
      : sortedTxns.length > 0
        ? new Date(sortedTxns[0].date)
        : new Date();
    let last = end ? new Date(end) : new Date();
    // Max 3 years for daily points to prevent memory crash, fallback to monthly if needed (simplified for now to just cap at 1000 days visually)
    if (last.getTime() - current.getTime() > 1000 * 60 * 60 * 24 * 1000) {
      current = new Date(last.getTime() - 1000 * 60 * 60 * 24 * 1000);
    }

    const dates: string[] = [];
    while (current <= last) {
      dates.push(current.toISOString().split("T")[0]);
      current.setDate(current.getDate() + 1);
    }
    if (dates.length === 0) dates.push(new Date().toISOString().split("T")[0]);

    let currentBalances: Record<number, number> = {};
    accounts.forEach((a) => (currentBalances[a.id] = 0));

    const balanceHistory: Record<string, Record<number, number>> = {};
    let txnIndex = 0;

    // Replay transactions
    for (const d of dates) {
      while (txnIndex < sortedTxns.length && sortedTxns[txnIndex].date <= d) {
        const t = sortedTxns[txnIndex];
        for (const e of t.entries) {
          const acc = accounts.find((a) => a.id === e.account_id);
          if (acc) {
            if (acc.type === "asset") {
              currentBalances[acc.id] += Number(e.debit) - Number(e.credit);
            } else if (acc.type === "liability") {
              currentBalances[acc.id] += Number(e.credit) - Number(e.debit);
            }
          }
        }
        txnIndex++;
      }
      balanceHistory[d] = { ...currentBalances };
    }

    const colors = [
      "rgb(52, 211, 153)", // emerald
      "rgb(244, 63, 94)", // rose
      "rgb(96, 165, 250)", // blue
      "rgb(167, 139, 250)", // purple
      "rgb(251, 146, 60)", // orange
      "rgb(250, 204, 21)", // yellow
      "rgb(45, 212, 191)", // teal
      "rgb(129, 140, 248)", // indigo
    ];

    const datasets = targetAccounts.map((acc, index) => {
      const color = colors[index % colors.length];
      return {
        label: acc.name,
        data: dates.map((d) =>
          acc.type === "liability" ? -balanceHistory[d][acc.id] : balanceHistory[d][acc.id]
        ),
        borderColor: color,
        backgroundColor: color.replace("rgb", "rgba").replace(")", ", 0.1)"),
        tension: 0.4,
        fill: true,
        pointRadius: 2,
        borderWidth: 2,
      };
    });

    return {
      labels: dates,
      datasets,
    };
  });

  let expenseBreakdown = $derived.by(() => {
    const breakdown: Record<number, number> = {};
    filteredTransactions.forEach(t => {
      t.entries.forEach(e => {
        const acc = accounts.find(a => a.id === e.account_id);
        if (acc && acc.type === 'expense') {
          breakdown[acc.id] = (breakdown[acc.id] || 0) + Number(e.debit);
        }
      });
    });
    return Object.entries(breakdown)
      .map(([id, amount]) => ({
        id: Number(id),
        name: accounts.find(a => a.id === Number(id))?.name || 'Unknown',
        amount
      }))
      .sort((a, b) => b.amount - a.amount);
  });

  let doughnutData = $derived({
    labels: expenseBreakdown.map(e => e.name),
    datasets: [{
      data: expenseBreakdown.map(e => e.amount),
      backgroundColor: [
        "rgb(96, 165, 250)", // blue
        "rgb(52, 211, 153)", // emerald
        "rgb(167, 139, 250)", // purple
        "rgb(251, 146, 60)", // orange
        "rgb(244, 63, 94)", // rose
        "rgb(45, 212, 191)", // teal
        "rgb(129, 140, 248)", // indigo
        "rgb(250, 204, 21)", // yellow
      ],
      borderWidth: 0,
      hoverOffset: 20
    }]
  });

  $effect(() => {
    // Initialize chart visible accounts if empty
    if (Object.keys(chartVisibleAccounts).length === 0 && accounts.length > 0) {
      accounts.forEach((a) => {
        if (a.type === "asset" || a.type === "liability") {
          chartVisibleAccounts[a.id] = true;
        }
      });
    }
  });

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "index",
      intersect: false,
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: "rgba(15, 23, 42, 0.9)",
        titleColor: "#94a3b8",
        bodyColor: "#f8fafc",
        borderColor: "#334155",
        borderWidth: 1,
        padding: 10,
        boxPadding: 4,
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
          drawBorder: false,
        },
        ticks: {
          color: "#64748b",
          maxTicksLimit: 8,
        },
      },
      y: {
        grid: {
          color: "#1e293b",
          drawBorder: false,
        },
        ticks: {
          color: "#64748b",
          callback: function (value: any) {
            return "$" + value;
          },
        },
      },
    },
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '70%',
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        backgroundColor: "rgba(15, 23, 42, 0.9)",
        titleFont: { size: 12, weight: 'bold' },
        bodyFont: { size: 12 },
        padding: 12,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          label: function(context: any) {
            const label = context.label || '';
            const value = context.parsed || 0;
            return ` ${label}: $${value.toFixed(2)}`;
          }
        }
      }
    }
  };

  let verifyMerchant = $state<string>("");
  let verifyDate = $state<string>("");
  let verifyTotal = $state<number>(0);
  let verifyFromAccountId = $state<number | null>(null);
  let verifyToAccountId = $state<number | null>(null);
  let verifyItems = $state<{ name: string; price: number }[]>([]);

  async function fetchReceiptImage(receiptId: number) {
    try {
      const response = await fetch(
        `${BASE_URL}/receipts/${receiptId}/download`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        },
      );
      if (!response.ok) throw new Error("Failed to load image");
      const blob = await response.blob();
      if (receiptImageUrl) URL.revokeObjectURL(receiptImageUrl);
      receiptImageUrl = URL.createObjectURL(blob);
    } catch (e) {
      console.error("Error fetching receipt image:", e);
    }
  }

  function addItem() {
    verifyItems = [...verifyItems, { name: "", price: 0 }];
  }

  function removeItem(index: number) {
    verifyItems = verifyItems.filter((_, i) => i !== index);
  }

  $effect(() => {
    // Keep verifyTotal in sync with items if items exist
    if (verifyItems.length > 0) {
      verifyTotal = Number(
        verifyItems
          .reduce((acc, item) => acc + (Number(item.price) || 0), 0)
          .toFixed(2),
      );
    }
  });

  // New Account Form State
  let newAccountName = $state("");
  let newAccountType = $state("asset");
  let newAccountCurrency = $state("USD");

  // New Transaction Form State
  let txnDate = $state(new Date().toISOString().split("T")[0]);
  let txnDescription = $state("");
  let txnFromAccountId = $state(null);
  let txnToAccountId = $state(null);
  let txnAmount = $state(0);

  onMount(async () => {
    if (!session.user) await session.init();
    if (!session.user) {
      goto("/login");
      return;
    }

    const savedCurrency = localStorage.getItem("defaultCurrency");
    if (savedCurrency) defaultCurrency = savedCurrency;
    else defaultCurrency = "CAD";

    await refreshData();
  });

  $effect(() => {
    if (showAddAccount && !newAccountCurrency) {
      newAccountCurrency = defaultCurrency;
    }
  });

  async function fetchPendingReceipts() {
    try {
      pendingReceipts = await api.get("/receipts/");
    } catch (err) {
      console.error("Failed to fetch pending receipts:", err);
    }
  }

  async function handleReprocessReceipts() {
    try {
      await api.post("/receipts/reprocess", {});
      await fetchPendingReceipts();
    } catch (err) {
      console.error("Failed to reprocess receipts:", err);
      alert("Failed to re-trigger processing.");
    }
  }

  async function handleReviewReceipt(receipt: any) {
    try {
      pendingReceipt = receipt;
      const parsed = JSON.parse(receipt.parsed_json || "{}");
      
      verifyExtractionMethod = parsed.extraction_method || "Tesseract OCR";
      potentialMatches = receipt.potential_matches || [];
      
      verifyMerchant = parsed.merchant || "";
      verifyDate = parsed.date || (new Date().toISOString().split("T")[0]);
      verifyTotal = Number(parsed.total) || 0;
      verifyItems = (parsed.items || []).map((item: any) => ({
        name: item.name,
        price: Number(item.price) || 0
      }));
      
      await fetchReceiptImage(receipt.id);
      
      // Reset match state
      isUpdatingMatch = false;
      matchTransactionId = null;
      
      showReceiptCenter = false;
      
      if (potentialMatches.length > 0) {
        showMatchModal = true;
      } else {
        showVerifyModal = true;
      }
    } catch (err) {
      console.error("Failed to review receipt:", err);
    }
  }

  $effect(() => {
    if (showReceiptCenter) {
      fetchPendingReceipts();
      const interval = setInterval(fetchPendingReceipts, 3000);
      return () => clearInterval(interval);
    }
  });

  async function refreshData() {
    loading = true;
    try {
      const [txnsData, accountsData, hhData, budgetsData, rulesData] = await Promise.all([
        api.get("/transactions/"),
        api.get("/accounts/"),
        api.get("/households/"),
        api.get("/budgets/"),
        api.get("/rules/"),
      ]);
      
      const unmatchedRes = await api.get("/imports/unmatched");
      unreconciledCount = unmatchedRes.length;
      
      transactions = txnsData;
      accounts = accountsData;
      household = hhData;
      currentUser = session.user;
      budgets = budgetsData;
      rules = rulesData;

      // Fetch variances for each budget
      for (const b of budgets) {
        budgetVariances[b.id] = await api.get(`/budgets/${b.id}/variance`);
      }
      
      // Also refresh pending receipts
      await fetchPendingReceipts();
    } catch (e) {
      console.error("Failed to fetch dashboard data", e);
    } finally {
      loading = false;
    }
  }

  async function handleAddAccount() {
    try {
      await api.post("/accounts/", {
        name: newAccountName,
        type: newAccountType,
        currency: newAccountCurrency,
      });
      showAddAccount = false;
      newAccountName = "";
      await refreshData();
    } catch (e: any) {
      alert(`Failed to create account: ${e.message}`);
    }
  }

  async function handleAddTransaction() {
    if (!txnFromAccountId || !txnToAccountId || txnAmount <= 0) {
      alert("Please select accounts and enter an amount.");
      return;
    }

    try {
      await api.post("/transactions/", {
        date: txnDate,
        description: txnDescription,
        entries: [
          { account_id: txnFromAccountId, debit: 0, credit: txnAmount },
          { account_id: txnToAccountId, debit: txnAmount, credit: 0 },
        ],
      });
      showAddTransaction = false;
      txnDescription = "";
      txnAmount = 0;
      await refreshData();
    } catch (e: any) {
      alert(`Failed to create transaction: ${e.message}`);
    }
  }

  async function handleFileUpload(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    isUploading = true;
    const formData = new FormData();
    if (input.files.length === 1) {
      formData.append("file", input.files[0]);
    } else {
      for (let i = 0; i < input.files.length; i++) {
        formData.append("files", input.files[i]);
      }
    }

    try {
      if (input.files.length === 1) {
        await api.postForm("/receipts/", formData);
      } else {
        await api.postForm("/receipts/batch", formData);
      }
      
      showReceiptCenter = true;
      input.value = "";
      await fetchPendingReceipts();
      
      // Reset match session state
      isUpdatingMatch = false;
      matchTransactionId = null;
    } catch (e: any) {
      alert(`Upload failed: ${e.message}`);
    } finally {
      isUploading = false;
    }
  }

  async function handleMatchAttach(transactionId: number) {
    const matchedTxn = transactions.find(t => t.id === transactionId);
    if (!matchedTxn) return;

    // Set up Verification Modal state for the match
    isUpdatingMatch = true;
    matchTransactionId = transactionId;
    
    // Identify accounts from the existing transaction to help pre-fill
    // In a standard 2-entry txn, one is debit (to) and one is credit (from)
    const expenseEntry = matchedTxn.entries.find((e: any) => Number(e.debit) > 0);
    const assetEntry = matchedTxn.entries.find((e: any) => Number(e.credit) > 0);
    
    if (expenseEntry) verifyToAccountId = expenseEntry.account_id;
    if (assetEntry) verifyFromAccountId = assetEntry.account_id;

    showMatchModal = false;
    showVerifyModal = true;
  }

  function skipMatchAndVerify() {
    showMatchModal = false;
    showVerifyModal = true;
  }

  async function handleVerifySubmit() {
    if (!verifyFromAccountId || !verifyToAccountId) {
      alert("Please select both accounts.");
      return;
    }

    try {
      const entries = [];
      // To: Account (Debits) - Detailed line items from AI
      if (verifyItems.length > 0) {
        verifyItems.forEach((item: any) => {
          entries.push({
            account_id: verifyToAccountId,
            debit: Number(item.price),
            credit: 0,
            description: item.name // Item name description
          });
        });
        
        // Handle any balance difference as an adjustment
        const itemsSum = verifyItems.reduce((acc: number, item: any) => acc + Number(item.price), 0);
        if (Math.abs(verifyTotal - itemsSum) > 0.001) {
          entries.push({
            account_id: verifyToAccountId,
            debit: Number((verifyTotal - itemsSum).toFixed(2)),
            credit: 0,
            description: "Uncategorized Adjustments"
          });
        }
      } else {
        // Fallback if no items
        entries.push({
          account_id: verifyToAccountId,
          debit: verifyTotal,
          credit: 0,
          description: verifyMerchant || "Direct Purchase"
        });
      }

      // From: Account (Credit) - The payment total
      entries.push({
        account_id: verifyFromAccountId,
        debit: 0,
        credit: verifyTotal,
        description: verifyMerchant || "Payment"
      });

      if (isUpdatingMatch && matchTransactionId) {
        // PATCH existing transaction
        await api.patch(`/transactions/${matchTransactionId}`, {
          date: verifyDate,
          description: verifyMerchant,
          entries: entries
        });
        // Link receipt
        await api.patch(`/receipts/${pendingReceipt.id}/attach`, {
          transaction_id: matchTransactionId
        });
      } else {
        // POST new transaction
        await api.post("/transactions/", {
          date: verifyDate,
          description: verifyMerchant,
          receipt_id: pendingReceipt.id,
          entries: entries,
        });
      }

      if (receiptImageUrl) {
        URL.revokeObjectURL(receiptImageUrl);
        receiptImageUrl = null;
      }
      
      showVerifyModal = false;
      
      const currentMatchId = matchTransactionId;
      isUpdatingMatch = false;
      matchTransactionId = null;
      
      await refreshData();
      
      // If we updated a specific transaction, open it for review
      if (currentMatchId) {
        const updated = transactions.find(t => t.id === currentMatchId);
        if (updated) {
          selectedTransaction = updated;
          showTransactionDetail = true;
          if (updated.receipt_id) await fetchReceiptImage(updated.receipt_id);
        }
      }
    } catch (e: any) {
      alert(`Failed to save transaction: ${e.message}`);
    }
  }

  async function handleAttachReceipt(event: Event) {
    if (!selectedTransaction) return;
    const txnId = selectedTransaction.id;
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    try {
      isAttachingReceipt = true;
      const file = input.files[0];
      const formData = new FormData();
      formData.append("file", file);

      const receipt = await api.postForm("/receipts/", formData);

      // Update transaction with receipt ID
      await api.patch(`/transactions/${txnId}`, {
        receipt_id: receipt.id,
      });

      // Refresh
      await refreshData();
      
      // Update modal state
      const updated = transactions.find((t) => t.id === txnId);
      if (updated) {
        selectedTransaction = updated;
        if (updated.receipt_id) await fetchReceiptImage(updated.receipt_id);
      }
      alert("Receipt attached successfully!");
    } catch (e: any) {
      alert(`Attachment failed: ${e.message}`);
    } finally {
      isAttachingReceipt = false;
    }
  }

  function startEditingTransaction() {
    isEditingTransaction = true;
    if (!selectedTransaction) return;
    editTransactionData = {
      description: selectedTransaction.description,
      date: selectedTransaction.date,
      entries: selectedTransaction.entries.map((e: any) => ({ ...e })),
    };
  }

  function cancelEditingTransaction() {
    isEditingTransaction = false;
    editTransactionData = null;
  }

  async function handleEditSubmit() {
    try {
      // Validate balance
      const totalDebit = editTransactionData.entries.reduce(
        (acc: number, e: any) => acc + (Number(e.debit) || 0),
        0,
      );
      const totalCredit = editTransactionData.entries.reduce(
        (acc: number, e: any) => acc + (Number(e.credit) || 0),
        0,
      );

      if (Math.abs(totalDebit - totalCredit) > 0.001) {
        alert(
          `Transaction unbalanced! Total Debits: ${totalDebit.toFixed(2)}, Total Credits: ${totalCredit.toFixed(2)}`,
        );
        return;
      }

      if (!selectedTransaction) return;
      const updated = await api.patch(
        `/transactions/${selectedTransaction.id}`,
        editTransactionData,
      );
      selectedTransaction = updated;
      isEditingTransaction = false;
      editTransactionData = null;
      await refreshData();
    } catch (e: any) {
      alert(`Failed to update transaction: ${e.message}`);
    }
  }

  function handleDeleteTransaction() {
    const txn = selectedTransaction;
    if (!txn) return;

    requestConfirm("Delete Transaction", "Permanently delete this transaction?", async () => {
      try {
        await api.delete(`/transactions/${txn.id}`);
        showTransactionDetail = false;
        await refreshData();
      } catch (e: any) {
        alert(`Delete failed: ${e.message}`);
      }
    });
  }

  function addEditEntry() {
    editTransactionData.entries = [
      ...editTransactionData.entries,
      { account_id: 0, debit: 0, credit: 0 },
    ];
  }

  function removeEditEntry(index: number) {
    editTransactionData.entries = editTransactionData.entries.filter(
      (_: any, i: number) => i !== index,
    );
  }

  // Household logic
  let inviteEmail = $state("");
  let inviteRole = $state("member");
  let isInviting = $state(false);

  async function handleInviteMember() {
    if (!inviteEmail) return;
    isInviting = true;
    try {
      const res = await api.post("/households/invite", { email: inviteEmail, role: inviteRole });
      inviteEmail = "";
      if (res.status === "invite_sent") {
        alert("User not found! An invitation has been sent to their email.");
      } else {
        alert("Member added successfully!");
      }
      // Refresh household data
      household = await api.get("/households/");
    } catch (e: any) {
      alert(`Failed to invite member: ${e.message}`);
    } finally {
      isInviting = false;
    }
  }

  function handleRemoveMember(userId: number) {
    requestConfirm(
      "Remove Member",
      "Are you sure you want to remove this member from the household?",
      async () => {
        try {
          await api.delete(`/households/member/${userId}`);
          household = await api.get("/households/");
        } catch (e: any) {
          alert(`Failed to remove member: ${e.message}`);
        }
      }
    );
  }

  // Budget management
  let newBudgetName = $state("");
  let newBudgetMonth = $state(new Date().getMonth() + 1);
  let newBudgetYear = $state(new Date().getFullYear());
  let showAddBudgetLine = $state(false);
  let showAddBudget = $state(false);
  let activeBudgetId = $state<number | null>(null);
  let newBudgetLineAccountId = $state<number | null>(null);
  let newBudgetLineAmount = $state<number>(0);

  async function handleCreateBudget() {
    try {
      await api.post("/budgets/", { 
        name: newBudgetName || `Budget ${newBudgetMonth}/${newBudgetYear}`,
        month: newBudgetMonth,
        year: newBudgetYear 
      });
      newBudgetName = "";
      await refreshData();
    } catch (e: any) {
      alert(`Failed to create budget: ${e.message}`);
    }
  }

  async function handleAddBudgetLine() {
    if (!activeBudgetId || !newBudgetLineAccountId) return;
    try {
      await api.post(`/budgets/${activeBudgetId}/lines`, {
        account_id: newBudgetLineAccountId,
        planned_amount: newBudgetLineAmount
      });
      showAddBudgetLine = false;
      newBudgetLineAccountId = null;
      newBudgetLineAmount = 0;
      await refreshData();
    } catch (e: any) {
      alert(`Failed to add budget line: ${e.message}`);
    }
  }

  async function handleDeleteBudget(id: number) {
    if (!confirm("Delete this budget?")) return;
    try {
      await api.delete(`/budgets/${id}`);
      await refreshData();
    } catch (e: any) {
      alert(`Failed to delete budget: ${e.message}`);
    }
  }

  // Rule management
  let showAddRule = $state(false);
  let newRulePriority = $state<number>(0);
  let newRuleMerchant = $state<string>("");
  let newRuleAccountId = $state<number | null>(null);

  async function handleCreateRule() {
    if (!newRuleMerchant || !newRuleAccountId) return;
    try {
      await api.post("/rules/", {
        priority: newRulePriority,
        condition_json: { merchant_contains: newRuleMerchant },
        action_json: { assign_account_id: newRuleAccountId },
        active: true
      });
      showAddRule = false;
      newRuleMerchant = "";
      newRuleAccountId = null;
      await refreshData();
    } catch (e: any) {
      alert(`Failed to create rule: ${e.message}`);
    }
  }

  async function toggleRule(rule: any) {
    try {
      await api.patch(`/rules/${rule.id}`, { active: !rule.active });
      await refreshData();
    } catch (e: any) {
      alert(`Failed to update rule: ${e.message}`);
    }
  }

  async function handleDeleteRule(id: number) {
    if (!confirm("Delete this rule?")) return;
    try {
      await api.delete(`/rules/${id}`);
      await refreshData();
    } catch (e: any) {
      alert(`Failed to delete rule: ${e.message}`);
    }
  }

  function startRuleFromTransaction(txn: any) {
    // Extract merchant by removing prefixes
    newRuleMerchant = txn.description
      .replace(/^\[AUTO\]\s*Receipt:\s*/, "")
      .replace(/^\[DRAFT REVIEW\]\s*Receipt:\s*/, "")
      .replace(/^Receipt:\s*/, "");
    
    // Find the primary expense account from entries
    const expenseEntry = txn.entries.find((e: any) => Number(e.debit) > 0);
    if (expenseEntry) {
      const acc = accounts.find(a => a.id === expenseEntry.account_id);
      if (acc && acc.type === 'expense') {
        newRuleAccountId = acc.id;
      }
    }
    
    showTransactionDetail = false;
    currentTab = 'rules';
    showAddRule = true;
  }

  // Format balances for UI display (inverts liability balances for intuition)
  function formatBalance(account: any): string {
    const val = Number(account.balance);
    if (val === 0) return "0.00";
    if (account.type === "liability") {
      return (val > 0 ? "-" : "") + Math.abs(val).toFixed(2);
    }
    return val.toFixed(2);
  }
</script>

<Navbar bind:showSettings={showSettings} />

<div class="max-w-6xl mx-auto p-6 space-y-8">
  <header class="flex justify-between items-end">
    <div class="flex flex-col md:flex-row md:items-end gap-6">
      <div>
        <h2 class="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p class="text-slate-500 text-sm">
          Welcome back to your financial control center.
        </p>
      </div>
      <div class="h-12 w-[1px] bg-slate-800 hidden md:block mx-2"></div>
      <div class="flex flex-col">
        <span
          class="text-[10px] font-bold text-slate-500 uppercase tracking-widest"
          >Your Net Worth</span
        >
        <div
          class="text-3xl font-black text-white tracking-tight flex items-baseline gap-1"
        >
          <span class="text-emerald-500 text-xl font-mono">$</span>
          {netWorth.toFixed(2)}
        </div>
        <div class="flex gap-3">
          <span class="text-[10px] text-emerald-500/80 font-bold"
            >Assets: ${assetAccounts
              .reduce((s, a) => s + Number(a.balance), 0)
              .toFixed(2)}</span
          >
          <span class="text-[10px] text-rose-500/80 font-bold"
            >Debts: ${liabilityAccounts
              .reduce((s, a) => s + Number(a.balance), 0)
              .toFixed(2)}</span
          >
        </div>
      </div>
    </div>

    <div class="flex flex-col gap-4 items-end">
      <div class="flex bg-slate-950/50 p-1 rounded-xl border border-slate-800/50">
        <button 
          onclick={() => currentTab = 'overview'}
          class="px-4 py-1.5 rounded-lg text-xs font-bold transition-all {currentTab === 'overview' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}"
        >
          Overview
        </button>
        <button 
          onclick={() => currentTab = 'budgets'}
          class="px-4 py-1.5 rounded-lg text-xs font-bold transition-all {currentTab === 'budgets' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}"
        >
          Budgets
        </button>
        <button 
          onclick={() => currentTab = 'rules'}
          class="px-4 py-1.5 rounded-lg text-xs font-bold transition-all {currentTab === 'rules' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}"
        >
          Rules
        </button>
        <button 
          onclick={() => { currentTab = 'bank-feed'; }}
          class="px-4 py-1.5 rounded-lg text-xs font-bold transition-all relative {currentTab === 'bank-feed' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}"
        >
          Bank Feed
          {#if unreconciledCount > 0}
            <span class="absolute -top-1 -right-1 w-4 h-4 bg-rose-500 text-[9px] text-white flex items-center justify-center rounded-full border-2 border-slate-900 animate-pulse">
              {unreconciledCount}
            </span>
          {/if}
        </button>
        <button 
          onclick={() => { showReceiptCenter = true; }}
          class="px-4 py-1.5 rounded-lg text-xs font-bold transition-all relative {showReceiptCenter ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}"
        >
          Receipt Center
          {#if pendingReceipts.length > 0}
            <span class="absolute -top-1 -right-1 w-4 h-4 bg-orange-500 text-[9px] text-white flex items-center justify-center rounded-full border-2 border-slate-900 animate-pulse">
              {pendingReceipts.length}
            </span>
          {/if}
        </button>
      </div>

      <div class="flex gap-3">
      <button
        onclick={() => (showAddTransaction = !showAddTransaction)}
        class="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl border border-slate-700 transition-all flex items-center gap-2"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-5 w-5"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fill-rule="evenodd"
            d="M11 5a1 1 0 10-2 0v3H6a1 1 0 100 2h3v3a1 1 0 102 0v-3h3a1 1 0 100-2h-3V5z"
            clip-rule="evenodd"
          />
        </svg>
        New Transaction
      </button>

      <button
        onclick={() => (showImportCenter = true)}
        class="px-6 py-3 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 font-semibold rounded-xl border border-blue-500/30 transition-all flex items-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd" />
        </svg>
        Import Bank CSV
      </button>

      <button
        onclick={() => (showAddAccount = !showAddAccount)}
        class="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl border border-slate-700 transition-all flex items-center gap-2"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-5 w-5"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fill-rule="evenodd"
            d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
            clip-rule="evenodd"
          />
        </svg>
        Add Account
      </button>

      <label
        for="receipt-upload"
        class="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl cursor-pointer shadow-lg shadow-blue-900/20 transition-all flex items-center gap-2 {isUploading
          ? 'opacity-50 pointer-events-none'
          : ''}"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-5 w-5 {isUploading ? 'animate-spin' : ''}"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          {#if isUploading}
            <path d="M21 12a9 9 0 11-6.219-8.56" />
          {:else}
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          {/if}
        </svg>
        {isUploading ? "Processing..." : "Upload Receipt"}
        <input
          id="receipt-upload"
          type="file"
          multiple
          class="hidden"
          accept="image/*"
          onchange={handleFileUpload}
          disabled={isUploading}
        />
      </label>
    </div>
  </header>

  {#if currentTab === 'overview'}
    <!-- Dashboard Toolbar & Filters -->
  <div
    class="flex justify-between items-center bg-slate-900/50 p-4 rounded-xl border border-slate-800"
  >
    <div class="flex flex-wrap items-center gap-3">
      <div
        class="flex items-center gap-2 bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-xl"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-4 w-4 text-slate-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          ><path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
          /></svg
        >
        <select
          bind:value={dateFilterPreset}
          class="bg-transparent text-sm font-medium text-slate-300 outline-none cursor-pointer"
        >
          <optgroup label="Relative Ranges">
            <option value="today">Today</option>
            <option value="yesterday">Yesterday</option>
            <option value="this-week">This Week</option>
            <option value="last-week">Last Week</option>
            <option value="this-month">This Month</option>
            <option value="last-month">Last Month</option>
            <option value="this-year">This Year</option>
            <option value="last-year">Last Year</option>
          </optgroup>
          <optgroup label="Quarters (This Year)">
            <option value="q1-this">Q1: Jan - Mar</option>
            <option value="q2-this">Q2: Apr - Jun</option>
            <option value="q3-this">Q3: Jul - Sep</option>
            <option value="q4-this">Q4: Oct - Dec</option>
          </optgroup>
          <optgroup label="Quarters (Last Year)">
            <option value="q1-last">Last Year Q1</option>
            <option value="q2-last">Last Year Q2</option>
            <option value="q3-last">Last Year Q3</option>
            <option value="q4-last">Last Year Q4</option>
          </optgroup>
          <optgroup label="Rolling Periods">
            <option value="last-3y">Last 3 Years</option>
            <option value="last-7y">Last 7 Years</option>
          </optgroup>
          <option value="custom">Custom Range...</option>
        </select>
      </div>

      {#if dateFilterPreset === "custom"}
        <div
          class="flex items-center gap-2 animate-in slide-in-from-right-2 duration-200"
        >
          <input
            type="date"
            bind:value={customStartDate}
            class="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-300 outline-none focus:border-blue-500 transition-colors"
          />
          <span class="text-slate-600 text-xs">to</span>
          <input
            type="date"
            bind:value={customEndDate}
            class="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-300 outline-none focus:border-blue-500 transition-colors"
          />
        </div>
      {/if}
    </div>

    <div
      class="flex items-center gap-2 text-xs text-slate-500 overflow-x-auto pb-2 md:pb-0"
    >
      {#each accounts.filter((a) => a.type === "asset" || a.type === "liability") as acc}
        <button
          onclick={() =>
            (chartVisibleAccounts[acc.id] = !chartVisibleAccounts[acc.id])}
          class="px-2 py-1 rounded border transition-colors whitespace-nowrap {chartVisibleAccounts[
            acc.id
          ]
            ? acc.type === 'asset'
              ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
              : 'bg-rose-500/20 border-rose-500/50 text-rose-400'
            : 'bg-slate-800 border-slate-700 text-slate-500'}"
        >
          {acc.name}
        </button>
      {/each}
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl h-[350px] lg:col-span-2 shadow-2xl">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-xs font-black text-slate-500 uppercase tracking-widest">Balance History</h3>
      </div>
      <div class="h-[250px]">
        <canvas
          use:chartAction={{ type: "line", data: chartData, options: chartOptions }}
        ></canvas>
      </div>
    </div>

    <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl h-[350px] shadow-2xl flex flex-col">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-xs font-black text-slate-500 uppercase tracking-widest">Expense Breakdown</h3>
      </div>
      {#if expenseBreakdown.length > 0}
        <div class="flex-1 relative min-h-0">
          <canvas use:chartAction={{ type: "doughnut", data: doughnutData, options: doughnutOptions }}></canvas>
        </div>
        <div class="mt-4 space-y-1 max-h-[80px] overflow-auto pr-2 custom-scrollbar">
          {#each expenseBreakdown.slice(0, 5) as item, i}
            <div class="flex justify-between items-center text-[10px]">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full" style="background-color: {doughnutData.datasets[0].backgroundColor[i % doughnutData.datasets[0].backgroundColor.length]}"></div>
                <span class="text-slate-400 font-bold truncate max-w-[100px]">{item.name}</span>
              </div>
              <span class="text-white font-mono">${item.amount.toFixed(2)}</span>
            </div>
          {/each}
        </div>
      {:else}
        <div class="flex-1 flex items-center justify-center text-slate-600 text-sm italic">
          No expenses in this period
        </div>
      {/if}
    </div>
  </div>

  {#if showAddTransaction}
    <div
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[60] flex items-center justify-center p-4 overflow-y-auto"
    >
      <section
        class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-5xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200"
      >
        <div
          class="p-6 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center"
        >
          <h3 class="text-xl font-bold text-blue-400">New Transaction</h3>
          <button
            onclick={() => (showAddTransaction = false)}
            class="p-2 hover:bg-slate-800 rounded-xl transition-colors text-slate-400"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              /></svg
            >
          </button>
        </div>
        <form onsubmit={handleAddTransaction} class="p-8 space-y-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label
                for="txn-date"
                class="block text-xs font-bold text-slate-500 uppercase mb-2"
                >Date</label
              >
              <input
                id="txn-date"
                type="date"
                bind:value={txnDate}
                required
                class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 outline-none focus:border-blue-500 transition-colors"
              />
            </div>
            <div>
              <label
                for="txn-description"
                class="block text-xs font-bold text-slate-500 uppercase mb-2"
                >Description</label
              >
              <input
                id="txn-description"
                bind:value={txnDescription}
                required
                class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 outline-none focus:border-blue-500 transition-colors"
                placeholder="e.g. Lunch at Joe's"
              />
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label
                for="txn-from"
                class="block text-xs font-bold text-slate-500 uppercase mb-2"
                >From (Credit)</label
              >
              <div class="flex gap-2">
                <select
                  id="txn-from"
                  bind:value={txnFromAccountId}
                  required
                  class="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 outline-none focus:border-blue-500 transition-colors"
                >
                  <option value={null}>Select Account</option>
                  {#each accounts as account}
                    <option value={account.id}
                      >{account.name} ({account.type})</option
                    >
                  {/each}
                </select>
                <button
                  type="button"
                  onclick={() => (showAddAccount = true)}
                  class="p-3 bg-slate-950 border border-slate-800 rounded-xl hover:border-blue-500/50 transition-all text-slate-400 hover:text-blue-400"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-5 w-5"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    ><path
                      fill-rule="evenodd"
                      d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                      clip-rule="evenodd"
                    /></svg
                  >
                </button>
              </div>
            </div>
            <div>
              <label
                for="txn-to"
                class="block text-xs font-bold text-slate-500 uppercase mb-2"
                >To (Debit)</label
              >
              <div class="flex gap-2">
                <select
                  id="txn-to"
                  bind:value={txnToAccountId}
                  required
                  class="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 outline-none focus:border-blue-500 transition-colors"
                >
                  <option value={null}>Select Account</option>
                  {#each accounts as account}
                    <option value={account.id}
                      >{account.name} ({account.type})</option
                    >
                  {/each}
                </select>
                <button
                  type="button"
                  onclick={() => (showAddAccount = true)}
                  class="p-3 bg-slate-950 border border-slate-800 rounded-xl hover:border-blue-500/50 transition-all text-slate-400 hover:text-blue-400"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-5 w-5"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    ><path
                      fill-rule="evenodd"
                      d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                      clip-rule="evenodd"
                    /></svg
                  >
                </button>
              </div>
            </div>
          </div>

          <div>
            <label
              for="txn-amount"
              class="block text-xs font-bold text-slate-500 uppercase mb-2"
              >Amount</label
            >
            <input
              id="txn-amount"
              type="number"
              step="0.01"
              bind:value={txnAmount}
              required
              class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-xl font-mono text-blue-400 outline-none focus:border-blue-500 transition-colors"
              placeholder="0.00"
            />
          </div>

          <div class="pt-4 flex gap-4">
            <button
              type="button"
              onclick={() => (showAddTransaction = false)}
              class="flex-1 py-4 bg-slate-800 hover:bg-slate-700 font-bold rounded-2xl transition-all"
              >Discard</button
            >
            <button
              type="submit"
              class="flex-[2] py-4 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl shadow-lg shadow-blue-500/20 transition-all"
              >Save Transaction</button
            >
          </div>
        </form>
      </section>
    </div>
  {/if}
  {#if showAddAccount}
    <div
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[70] flex items-center justify-center p-4 overflow-y-auto"
    >
      <section
        class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200"
      >
        <div
          class="p-6 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center"
        >
          <h3 class="text-xl font-bold text-blue-400">Create New Account</h3>
          <button
            onclick={() => (showAddAccount = false)}
            class="p-2 hover:bg-slate-800 rounded-xl transition-colors text-slate-400"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              /></svg
            >
          </button>
        </div>
        <form onsubmit={handleAddAccount} class="p-8 space-y-6">
          <div>
            <label
              for="acc-name"
              class="block text-xs font-bold text-slate-500 uppercase mb-2"
              >Account Name</label
            >
            <input
              id="acc-name"
              bind:value={newAccountName}
              required
              class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 outline-none focus:border-blue-500 transition-colors"
              placeholder="e.g. Checking"
            />
          </div>
          <div>
            <label
              for="acc-type"
              class="block text-xs font-bold text-slate-500 uppercase mb-2"
              >Type</label
            >
            <select
              id="acc-type"
              bind:value={newAccountType}
              class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 outline-none focus:border-blue-500 transition-colors"
            >
              <option value="asset">Asset (Bank, Cash)</option>
              <option value="liability">Liability (Credit Card, Loan)</option>
              <option value="income">Income (Salary, Interest)</option>
              <option value="expense">Expense (Food, Rent)</option>
              <option value="equity">Equity</option>
            </select>
          </div>
          <div>
            <label
              for="acc-currency"
              class="block text-xs font-bold text-slate-500 uppercase mb-2"
              >Currency</label
            >
            <input
              id="acc-currency"
              bind:value={newAccountCurrency}
              class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 outline-none focus:border-blue-500 transition-colors"
              placeholder="USD"
            />
          </div>
          <div class="pt-4 flex gap-4">
            <button
              type="button"
              onclick={() => (showAddAccount = false)}
              class="flex-1 py-4 bg-slate-800 hover:bg-slate-700 font-bold rounded-2xl transition-all"
              >Cancel</button
            >
            <button
              type="submit"
              class="flex-1 py-4 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl shadow-lg shadow-blue-500/20 transition-all"
              >Create Account</button
            >
          </div>
        </form>
      </section>
    </div>
  {/if}

  {#if confirmState.show}
    <div
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
    >
      <div
        class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-sm shadow-2xl p-6 text-center animate-in zoom-in-95 duration-200"
      >
        <h3 class="text-xl font-bold mb-2 text-white">{confirmState.title}</h3>
        <p class="text-slate-400 mb-6 text-sm">{confirmState.message}</p>
        <div class="flex gap-3">
          <button
            onclick={() => (confirmState.show = false)}
            class="flex-1 py-3 px-4 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-xl transition-colors"
          >
            Cancel
          </button>
          <button
            onclick={() => {
              confirmState.show = false;
              confirmState.onConfirm();
            }}
            class="flex-1 py-3 px-4 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-xl transition-colors"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  {/if}

  {#if showMatchModal}
    <div
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[60] flex items-center justify-center p-4"
    >
      <div
        class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200"
      >
        <div class="p-6 text-center">
          <div
            class="w-16 h-16 bg-blue-500/10 text-blue-400 rounded-full flex items-center justify-center mx-auto mb-4"
          >
            <svg
              class="w-8 h-8"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
              /></svg
            >
          </div>
          <h3 class="text-xl font-bold mb-2 text-white">Match Found!</h3>
          <p class="text-slate-400 mb-6 text-sm">
            We think we found a matching transaction for this receipt. Would you like to attach the photo and link them?
          </p>
          <div class="space-y-3 mb-6 max-h-[300px] overflow-y-auto">
            {#each potentialMatches as match}
              <button
                onclick={() => handleMatchAttach(match.id)}
                class="w-full p-4 bg-slate-950 border border-slate-800 hover:border-blue-500/50 rounded-2xl flex items-center justify-between group transition-all"
              >
                <div class="text-left">
                  <div class="text-slate-300 font-medium group-hover:text-blue-400 transition-colors">
                    {match.description}
                  </div>
                  <div class="text-xs text-slate-500 mt-1">
                    {new Date(match.date).toLocaleDateString()}
                  </div>
                </div>
                <div class="text-emerald-400 font-mono">
                  ${match.entries.reduce((acc: number, e: any) => acc + (Number(e.debit) || 0), 0).toFixed(2)}
                </div>
              </button>
            {/each}
          </div>
          <div class="flex gap-3">
            <button
              onclick={skipMatchAndVerify}
              class="flex-1 py-3 px-4 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-xl transition-colors"
            >
              Skip & Create New
            </button>
          </div>
        </div>
      </div>
    </div>
  {/if}

  {#if showVerifyModal}
    <div
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto"
    >
      <div
        class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-6xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col md:flex-row h-[90vh]"
      >
        <!-- Left Pane: Image -->
        <div
          class="flex-1 bg-slate-950 border-r border-slate-800 flex flex-col relative overflow-hidden"
        >
          <div
            class="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50"
          >
            <h4 class="text-xs font-bold text-slate-500 uppercase">
              Receipt Preview
            </h4>
            <div class="flex gap-2">
              {#if verifyExtractionMethod.includes('Gemini')}
                <span class="text-[10px] text-blue-200 bg-blue-600/50 border border-blue-500/50 px-2 py-1 rounded shadow-[0_0_10px_rgba(59,130,246,0.5)]">✨ {verifyExtractionMethod}</span>
              {:else if verifyExtractionMethod}
                <span class="text-[10px] text-slate-300 bg-slate-700 px-2 py-1 rounded border border-slate-600">📄 {verifyExtractionMethod}</span>
              {/if}
              <span
                class="text-[10px] text-slate-400 bg-slate-800 px-2 py-1 rounded border border-slate-700"
                >Encrypted Storage</span
              >
            </div>
          </div>
          <div class="flex-1 overflow-auto p-4 flex bg-checkered">
            {#if receiptImageUrl}
              <img
                src={receiptImageUrl}
                alt="Receipt Content"
                class="max-w-full shadow-2xl rounded-sm m-auto"
                oncontextmenu={(e) => e.preventDefault()}
              />
            {:else if pendingReceipt}
              <div class="text-slate-700 animate-pulse">Loading preview...</div>
            {:else}
              <div class="text-slate-800 italic text-sm">No image data</div>
            {/if}
          </div>
        </div>

        <!-- Right Pane: Form -->
        <div class="flex-1 flex flex-col bg-slate-900 overflow-hidden">
          <div
            class="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50"
          >
            <div>
              <h3 class="text-xl font-bold">Verify & Settle</h3>
              <p class="text-slate-400 text-xs">
                Line items extracted via OCR. Adjust as needed.
              </p>
            </div>
            <button
              onclick={() => {
                showVerifyModal = false;
                if (receiptImageUrl) {
                  URL.revokeObjectURL(receiptImageUrl);
                  receiptImageUrl = null;
                }
              }}
              aria-label="Close"
              class="p-2 hover:bg-slate-800 rounded-xl transition-colors"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                ><path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                /></svg
              >
            </button>
          </div>

          <form
            onsubmit={handleVerifySubmit}
            class="flex-1 flex flex-col overflow-hidden"
          >
            <div class="flex-1 overflow-y-auto p-8 space-y-8">
              <!-- General Info -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label
                    for="verify-merchant"
                    class="block text-[10px] font-bold text-slate-500 uppercase mb-2"
                    >Merchant / Description</label
                  >
                  <input
                    id="verify-merchant"
                    bind:value={verifyMerchant}
                    required
                    class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 outline-none focus:border-blue-500 transition-all"
                  />
                </div>
                <div>
                  <label
                    for="verify-date"
                    class="block text-[10px] font-bold text-slate-500 uppercase mb-2"
                    >Date</label
                  >
                  <input
                    id="verify-date"
                    type="date"
                    bind:value={verifyDate}
                    required
                    class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <!-- Line Items -->
              <div class="space-y-4">
                <div class="flex justify-between items-center">
                  <h4
                    class="text-[10px] font-bold text-blue-500 uppercase tracking-widest"
                  >
                    Line Items Breakdown
                  </h4>
                  <button
                    type="button"
                    onclick={addItem}
                    class="text-[10px] bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 px-3 py-1 rounded-full font-bold transition-all"
                    >+ Add Item</button
                  >
                </div>

                <div
                  class="space-y-2 max-h-64 overflow-y-auto pr-2 custom-scrollbar"
                >
                  {#each verifyItems as item, i}
                    <div
                      class="flex gap-2 items-center animate-in slide-in-from-right-4"
                    >
                      <input
                        placeholder="Item name"
                        bind:value={item.name}
                        class="flex-[3] bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500"
                      />
                      <input
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        bind:value={item.price}
                        class="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-right font-mono outline-none focus:border-blue-500"
                      />
                      <button
                        type="button"
                        onclick={() => removeItem(i)}
                        aria-label="Remove item"
                        class="p-2 text-slate-600 hover:text-red-400 transition-colors"
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          class="h-4 w-4"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                          ><path
                            fill-rule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z"
                            clip-rule="evenodd"
                          /></svg
                        >
                      </button>
                    </div>
                  {/each}
                  {#if verifyItems.length === 0}
                    <div
                      class="p-8 border-2 border-dashed border-slate-800 rounded-2xl flex flex-col items-center justify-center text-slate-600"
                    >
                      <p class="text-xs">No line items added</p>
                    </div>
                  {/if}
                </div>
              </div>

              <!-- Account Assignment & Total -->
              <div
                class="p-6 bg-slate-950 border border-slate-800 rounded-2xl space-y-6"
              >
                <div class="grid grid-cols-2 gap-6">
                  <div>
                    <label
                      for="verify-from"
                      class="block text-[10px] font-bold text-slate-500 uppercase mb-2"
                      >From (Credit)</label
                    >
                    <div class="flex gap-2">
                      <select
                        id="verify-from"
                        bind:value={verifyFromAccountId}
                        required
                        class="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500"
                      >
                        <option value={null}>Select Account</option>
                        {#each accounts as account}
                          <option value={account.id}
                            >{account.name} ({formatBalance(account)}
                            2, )})</option
                          >
                        {/each}
                      </select>
                      <button
                        type="button"
                        onclick={() => (showAddAccount = true)}
                        class="p-2 bg-slate-800 border border-slate-700 rounded-xl hover:border-slate-500 transition-all text-slate-400"
                        title="Quick Add Account"
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          class="h-4 w-4"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                          ><path
                            fill-rule="evenodd"
                            d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                            clip-rule="evenodd"
                          /></svg
                        >
                      </button>
                    </div>
                  </div>
                  <div>
                    <label
                      for="verify-to"
                      class="block text-[10px] font-bold text-slate-500 uppercase mb-2"
                      >To (Debit)</label
                    >
                    <div class="flex gap-2">
                      <select
                        id="verify-to"
                        bind:value={verifyToAccountId}
                        required
                        class="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500"
                      >
                        <option value={null}>Select Account</option>
                        {#each accounts as account}
                          <option value={account.id}
                            >{account.name} ({formatBalance(account)}
                            2, )})</option
                          >
                        {/each}
                      </select>
                      <button
                        type="button"
                        onclick={() => (showAddAccount = true)}
                        class="p-2 bg-slate-800 border border-slate-700 rounded-xl hover:border-slate-500 transition-all text-slate-400"
                        title="Quick Add Account"
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          class="h-4 w-4"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                          ><path
                            fill-rule="evenodd"
                            d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                            clip-rule="evenodd"
                          /></svg
                        >
                      </button>
                    </div>
                  </div>
                </div>

                <div
                  class="flex justify-between items-end pt-4 border-t border-slate-800"
                >
                  <div class="text-[10px] text-slate-500 font-bold uppercase">
                    Total Amount
                  </div>
                  {#if verifyItems.length > 0}
                    <div class="text-3xl font-mono font-bold text-blue-500">
                      ${verifyTotal.toFixed(2)}
                    </div>
                  {:else}
                    <div class="flex items-center gap-2">
                      <span class="text-blue-500 font-mono text-xl">$</span>
                      <input
                        type="number"
                        step="0.01"
                        bind:value={verifyTotal}
                        class="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-right font-mono text-xl text-blue-500 outline-none focus:border-blue-500 w-32"
                      />
                    </div>
                  {/if}
                </div>
              </div>
            </div>

            <div class="p-8 bg-slate-900 border-t border-slate-800 flex gap-4">
              <button
                type="button"
                onclick={() => (showVerifyModal = false)}
                class="flex-1 py-4 bg-slate-800 hover:bg-slate-700 font-bold rounded-2xl transition-all"
                >Discard</button
              >
              <button
                type="submit"
                class="flex-[2] py-4 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl shadow-lg shadow-blue-500/20 transition-all"
                >{isUpdatingMatch ? "Update & Match" : "Confirm & Settle"}</button
              >
            </div>
          </form>
        </div>
      </div>
    </div>
  {/if}

  {#if showReceiptCenter}
    <div class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[70] flex items-center justify-center p-4">
      <div class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh] animate-in zoom-in-95 duration-200">
        <div class="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
          <div class="flex items-center gap-3">
            <h3 class="text-xl font-bold text-orange-400">Receipt Center</h3>
            <span class="px-2 py-0.5 bg-orange-500/10 border border-orange-500/20 text-orange-400 text-[10px] uppercase font-black rounded-full">
              {pendingReceipts.length} Total
            </span>
            {#if pendingReceipts.some(r => r.status === 'pending' || r.status === 'failed')}
              <button 
                onclick={handleReprocessReceipts}
                class="px-2 py-1 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-[10px] font-bold rounded-lg transition-all flex items-center gap-1"
                title="Re-trigger AI parsing for pending or failed receipts"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Reprocess Stuck
              </button>
            {/if}
          </div>
          <button onclick={() => showReceiptCenter = false} class="p-2 hover:bg-slate-800 rounded-xl transition-colors text-slate-400">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="flex-1 overflow-auto p-6 space-y-4 custom-scrollbar">
          {#if pendingReceipts.length === 0}
            <div class="text-center py-12">
              <div class="w-16 h-16 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <p class="text-slate-500 italic">No pending receipts to review.</p>
            </div>
          {:else}
            {#each pendingReceipts as receipt}
              <div class="bg-slate-950 border border-slate-800/50 p-4 rounded-2xl flex items-center justify-between group hover:border-blue-500/50 transition-all">
                <div class="flex items-center gap-4">
                  <div class="w-12 h-12 bg-slate-900 rounded-lg flex items-center justify-center text-slate-500">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div>
                    <h4 class="text-sm font-bold text-white truncate max-w-[200px]">{receipt.original_filename}</h4>
                    <p class="text-[10px] text-slate-500">{new Date(receipt.created_at).toLocaleString()}</p>
                    <div class="mt-1 flex items-center gap-2">
                       {#if receipt.status === 'pending'}
                         <span class="text-[10px] text-slate-500 flex items-center gap-1"><div class="w-1.5 h-1.5 rounded-full bg-slate-500"></div> Pending</span>
                       {:else if receipt.status === 'processing'}
                         <span class="text-[10px] text-blue-400 flex items-center gap-1 animate-pulse"><div class="w-1.5 h-1.5 rounded-full bg-blue-500"></div> AI Processing...</span>
                       {:else if receipt.status === 'processed'}
                         <span class="text-[10px] text-emerald-400 flex items-center gap-1"><div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div> Ready to Review</span>
                       {:else if receipt.status === 'failed'}
                         <span class="text-[10px] text-rose-400 flex items-center gap-1"><div class="w-1.5 h-1.5 rounded-full bg-rose-500"></div> AI Parsing Failed</span>
                       {/if}
                    </div>
                  </div>
                </div>
                
                <div class="flex items-center gap-2">
                  {#if receipt.status === 'processed' || receipt.status === 'failed'}
                    <button 
                      onclick={() => handleReviewReceipt(receipt)}
                      class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl transition-all shadow-lg shadow-blue-900/20"
                    >
                      Review
                    </button>
                  {/if}
                  <button 
                    onclick={() => requestConfirm("Delete Receipt", "Are you sure you want to delete this receipt?", async () => {
                      await api.delete(`/receipts/${receipt.id}`);
                      await fetchPendingReceipts();
                    })}
                    class="p-2 hover:bg-rose-500/10 text-slate-600 hover:text-rose-500 rounded-lg transition-colors"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            {/each}
          {/if}
        </div>
      </div>
    </div>
  {/if}

  {#if filterAccountId}
    <div
      class="mb-4 flex items-center justify-between bg-blue-500/10 border border-blue-500/30 p-4 rounded-2xl"
    >
      <div class="text-blue-400 text-sm font-medium">
        Showing transactions for: <span class="font-bold underline"
          >{accounts.find((a) => a.id === filterAccountId)?.name}</span
        >
      </div>
      <button
        onclick={() => (filterAccountId = null)}
        class="text-[10px] font-bold uppercase text-blue-400 hover:text-white transition-colors"
        >Clear Filter</button
      >
    </div>
  {/if}

  {#if showTransactionDetail && selectedTransaction}
    <div
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto"
    >
      <div
        class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-4xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200"
      >
        <div
          class="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50"
        >
          <div class="flex items-center gap-4">
            <div>
              <h3 class="text-xl font-bold">Transaction Details</h3>
              <p class="text-slate-400 text-xs">
                ID: {selectedTransaction.id} • {selectedTransaction.date}
              </p>
            </div>
            {#if !isEditingTransaction}
              <button
                onclick={startEditingTransaction}
                class="px-4 py-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-full text-xs font-bold transition-all flex items-center gap-2"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-3 w-3"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  ><path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  /></svg
                >
                Edit
              </button>
              <button
                onclick={() => startRuleFromTransaction(selectedTransaction)}
                class="px-4 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-500 border border-amber-500/30 rounded-full text-xs font-bold transition-all flex items-center gap-2"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
                Create Rule
              </button>
              <button
                onclick={handleDeleteTransaction}
                class="px-4 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 border border-rose-500/30 rounded-full text-xs font-bold transition-all flex items-center gap-2"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete
              </button>
            {:else}
              <div class="flex items-center gap-2">
                <button
                  onclick={handleEditSubmit}
                  class="px-4 py-1.5 bg-emerald-500 text-white rounded-full text-xs font-bold transition-all shadow-lg shadow-emerald-500/20"
                >
                  Save Changes
                </button>
                <button
                  onclick={cancelEditingTransaction}
                  class="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-full text-xs font-bold transition-all"
                >
                  Cancel
                </button>
              </div>
            {/if}
          </div>
          <button
            onclick={() => {
              showTransactionDetail = false;
              isEditingTransaction = false;
            }}
            aria-label="Close"
            class="p-2 hover:bg-slate-800 rounded-xl transition-colors text-slate-400"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              /></svg
            >
          </button>
        </div>

        <div class="flex flex-col md:flex-row h-[60vh]">
          <!-- Entries List / Edit Form -->
          <div class="flex-1 p-6 overflow-auto border-r border-slate-800">
            {#if !isEditingTransaction}
              <h4
                class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4"
              >
                Entries Breakdown
              </h4>
              <div class="space-y-3">
                {#each selectedTransaction.entries as entry}
                  <div
                    class="bg-slate-950 p-4 rounded-xl border border-slate-800"
                  >
                    <div class="flex justify-between items-start">
                      <div class="flex flex-col">
                        <span class="font-medium text-slate-300">
                          {entry.description || (accounts.find((a) => a.id === entry.account_id)?.name || "Unknown")}
                        </span>
                        {#if entry.description}
                          <span class="text-[10px] text-slate-600 uppercase tracking-tight">
                            {accounts.find((a) => a.id === entry.account_id)?.name || "Account"}
                          </span>
                        {/if}
                      </div>
                      <div class="font-mono text-sm mt-1">
                        {#if Number(entry.debit) > 0}
                          <span class="text-emerald-400">+{Number(entry.debit).toFixed(2)} DR</span>
                        {:else if Number(entry.credit) > 0}
                          <span class="text-rose-400">-{Number(entry.credit).toFixed(2)} CR</span>
                        {:else}
                          <span class="text-slate-600">0.00</span>
                        {/if}
                      </div>
                    </div>
                    {#if !entry.description}
                      <div class="text-[10px] text-slate-600 uppercase mt-1">
                        {accounts.find((a) => a.id === entry.account_id)?.type || "Account"}
                      </div>
                    {/if}
                  </div>
                {/each}
              </div>

              <div
                class="mt-8 p-4 bg-blue-500/5 border border-blue-500/10 rounded-xl"
              >
                <div class="flex justify-between items-center">
                  <span class="text-xs font-bold text-blue-400 uppercase"
                    >Description</span
                  >
                  <span class="text-sm font-medium"
                    >{selectedTransaction.description}</span
                  >
                </div>
              </div>
            {:else}
              <div class="space-y-6">
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label
                      for="edit-date"
                      class="block text-[10px] font-bold text-slate-500 uppercase mb-2"
                      >Date</label
                    >
                    <input
                      type="date"
                      id="edit-date"
                      bind:value={editTransactionData.date}
                      class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm outline-none focus:border-blue-500 transition-colors"
                    />
                  </div>
                  <div>
                    <label
                      for="edit-desc"
                      class="block text-[10px] font-bold text-slate-500 uppercase mb-2"
                      >Description</label
                    >
                    <input
                      type="text"
                      id="edit-desc"
                      bind:value={editTransactionData.description}
                      class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm outline-none focus:border-blue-500 transition-colors"
                    />
                  </div>
                </div>

                <div>
                  <div class="flex justify-between items-center mb-4">
                    <h4
                      class="text-[10px] font-bold text-slate-500 uppercase tracking-widest"
                    >
                      Entries
                    </h4>
                    <button
                      onclick={addEditEntry}
                      class="text-[10px] font-bold text-blue-400 hover:text-blue-300 uppercase tracking-widest flex items-center gap-1"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-3 w-3"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        ><path
                          fill-rule="evenodd"
                          d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                          clip-rule="evenodd"
                        /></svg
                      > Add Entry
                    </button>
                  </div>

                  <div class="space-y-3">
                    {#each editTransactionData.entries as entry, i}
                      <div
                        class="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-4"
                      >
                        <div class="flex gap-4">
                          <div class="flex-1">
                            <select
                              bind:value={entry.account_id}
                              class="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs outline-none focus:border-blue-500"
                            >
                              <option value={0}>Select Account...</option>
                              {#each accounts as acc}
                                <option value={acc.id}>{acc.name}</option>
                              {/each}
                            </select>
                          </div>
                          <button
                            onclick={() => removeEditEntry(i)}
                            class="text-slate-600 hover:text-red-400 trasition-colors"
                          >
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              class="h-4 w-4"
                              viewBox="0 0 20 20"
                              fill="currentColor"
                              ><path
                                fill-rule="evenodd"
                                d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z"
                                clip-rule="evenodd"
                              /></svg
                            >
                          </button>
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                          <div class="space-y-1">
                            <label
                              class="text-[9px] font-bold text-slate-600 uppercase"
                              >Debit (+)</label
                            >
                            <input
                              type="number"
                              step="0.01"
                              bind:value={entry.debit}
                              class="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-emerald-400 outline-none focus:border-emerald-500"
                            />
                          </div>
                          <div class="space-y-1">
                            <label
                              class="text-[9px] font-bold text-slate-600 uppercase"
                              >Credit (-)</label
                            >
                            <input
                              type="number"
                              step="0.01"
                              bind:value={entry.credit}
                              class="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-rose-400 outline-none focus:border-rose-500"
                            />
                          </div>
                        </div>
                      </div>
                    {/each}
                  </div>
                </div>
              </div>
            {/if}
          </div>

          <!-- Receipt Management -->
          <div class="flex-1 bg-slate-950 flex flex-col overflow-hidden">
            <div
              class="p-4 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center"
            >
              <span class="text-[10px] font-bold text-slate-500 uppercase"
                >Attached Receipt</span
              >
              {#if !selectedTransaction.receipt_id}
                <label
                  class="text-[10px] bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded-full font-bold transition-all cursor-pointer"
                >
                  {isAttachingReceipt ? "Uploading..." : "Attach Receipt"}
                  <input
                    type="file"
                    multiple
                    class="hidden"
                    accept="image/*"
                    onchange={handleAttachReceipt}
                    disabled={isAttachingReceipt}
                  />
                </label>
              {/if}
            </div>
            <div class="flex-1 overflow-auto bg-checkered flex p-4">
              {#if receiptImageUrl}
                <img
                  src={receiptImageUrl}
                  alt="Receipt"
                  class="max-w-full shadow-2xl rounded-sm m-auto"
                />
              {:else if selectedTransaction.receipt_id}
                <div class="text-slate-600 animate-pulse text-xs">
                  Loading receipt image...
                </div>
              {:else}
                <div class="text-center p-8">
                  <div
                    class="w-16 h-16 bg-slate-900 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-700"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      class="h-8 w-8"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      ><path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                      /></svg
                    >
                  </div>
                  <p class="text-slate-600 text-sm">
                    No receipt attached to this transaction.
                  </p>
                </div>
              {/if}
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}

  <div class="space-y-8">
    {#if assetAccounts.length > 0}
      <div>
        <h4
          class="text-[10px] font-bold text-emerald-500 uppercase tracking-widest mb-4"
        >
          Assets & Cash
        </h4>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          {#each assetAccounts as account}
            <button
              onclick={() => (filterAccountId = account.id)}
              class="p-6 bg-slate-900 rounded-2xl border border-slate-800 hover:border-emerald-500/50 transition-all text-left group"
            >
              <div class="text-[10px] font-bold uppercase text-slate-500 mb-1">
                {account.type}
              </div>
              <div
                class="text-lg font-semibold group-hover:text-emerald-400 transition-colors"
              >
                {account.name}
              </div>
              <div class="text-2xl font-mono mt-2 text-white">
                <span class="text-slate-600 text-sm">{account.currency}</span>
                {formatBalance(account)}
              </div>
            </button>
          {/each}
        </div>
      </div>
    {/if}

    {#if liabilityAccounts.length > 0}
      <div>
        <h4
          class="text-[10px] font-bold text-rose-500 uppercase tracking-widest mb-4"
        >
          Debts & Liabilities
        </h4>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          {#each liabilityAccounts as account}
            <button
              onclick={() => (filterAccountId = account.id)}
              class="p-6 bg-slate-900 rounded-2xl border border-slate-800 hover:border-rose-500/50 transition-all text-left group"
            >
              <div class="text-[10px] font-bold uppercase text-slate-500 mb-1">
                {account.type}
              </div>
              <div
                class="text-lg font-semibold group-hover:text-rose-400 transition-colors"
              >
                {account.name}
              </div>
              <div class="text-2xl font-mono mt-2 text-white">
                <span class="text-slate-600 text-sm">{account.currency}</span>
                {formatBalance(account)}
              </div>
            </button>
          {/each}
        </div>
      </div>
    {/if}

    {#if trackingAccounts.length > 0}
      <div>
        <h4
          class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4"
        >
          Tracking (Income & Expenses)
        </h4>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          {#each trackingAccounts as account}
            <button
              onclick={() => (filterAccountId = account.id)}
              class="p-6 bg-slate-900 rounded-2xl border border-slate-800 hover:border-blue-500/50 transition-all text-left group"
            >
              <div class="text-[10px] font-bold uppercase text-slate-500 mb-1">
                {account.type}
              </div>
              <div
                class="text-lg font-semibold group-hover:text-blue-400 transition-colors"
              >
                {account.name}
              </div>
              <div class="text-2xl font-mono mt-2 text-slate-400">
                <span class="text-slate-600 text-sm">{account.currency}</span>
                {formatBalance(account)}
              </div>
            </button>
          {/each}
        </div>
      </div>
    {/if}
  </div>

  <section
    class="bg-slate-900 rounded-3xl border border-slate-800 overflow-hidden shadow-xl"
  >
    <div
      class="p-6 border-b border-slate-800 flex flex-col md:flex-row gap-4 md:items-center justify-between bg-slate-900/50"
    >
      <div class="flex items-baseline gap-3">
        <h3 class="text-xl font-bold">Recent Transactions</h3>
        {#if filterAccountId}
          <button
            onclick={() => (filterAccountId = null)}
            class="text-[10px] font-bold text-blue-400 uppercase tracking-widest hover:text-blue-300 transition-colors"
          >
            Clear Account Filter
          </button>
        {/if}
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="w-full text-left">
        <thead>
          <tr
            class="bg-slate-950 text-slate-500 text-xs uppercase tracking-tighter"
          >
            <th class="px-6 py-4">Date</th>
            <th class="px-6 py-4">Description</th>
            <th class="px-6 py-4">Status</th>
            <th class="px-6 py-4 text-right">Amount</th>
          </tr>
        </thead>
        <tbody>
          {#if loading}
            {#each Array(5) as _}
              <tr class="animate-pulse">
                <td class="px-6 py-4"
                  ><div class="h-4 w-20 bg-slate-800 rounded"></div></td
                >
                <td class="px-6 py-4"
                  ><div class="h-4 w-40 bg-slate-800 rounded"></div></td
                >
                <td class="px-6 py-4"
                  ><div class="h-4 w-12 bg-slate-800 rounded"></div></td
                >
                <td class="px-6 py-4"
                  ><div class="h-4 w-16 bg-slate-800 ml-auto rounded"></div></td
                >
              </tr>
            {/each}
          {:else if transactions.length === 0}
            <tr>
              <td colspan="4" class="px-6 py-12 text-center text-slate-500">
                No transactions yet. Upload a receipt or add one manually.
              </td>
            </tr>
          {:else}
            {#each filteredTransactions as txn}
              <tr
                onclick={() => {
                  selectedTransaction = txn;
                  showTransactionDetail = true;
                  if (txn.receipt_id) fetchReceiptImage(txn.receipt_id);
                  else receiptImageUrl = null;
                }}
                class="border-t border-slate-800 hover:bg-slate-800/50 transition-colors cursor-pointer group"
              >
                <td class="px-6 py-4 text-sm font-mono text-slate-400"
                  >{txn.date}</td
                >
                <td
                  class="px-6 py-4 font-medium group-hover:text-blue-400 transition-colors"
                >
                  {txn.description}
                  {#if txn.receipt_id}
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      class="h-3 w-3 inline ml-1 text-slate-500"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      ><path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
                      /></svg
                    >
                  {/if}
                </td>
                <td class="px-6 py-4">
                  {#if txn.description.includes("[DRAFT]")}
                    <span
                      class="px-2 py-1 bg-amber-500/10 text-amber-500 rounded text-[10px] font-bold border border-amber-500/30"
                      >DRAFT</span
                    >
                  {:else}
                    <span
                      class="px-2 py-1 bg-blue-500/10 text-blue-500 rounded text-[10px] font-bold border border-blue-500/30"
                      >SETTLED</span
                    >
                  {/if}
                </td>
                <td
                  class="px-6 py-4 text-right font-mono font-bold text-lg text-slate-200"
                >
                  {Number(
                    txn.entries.reduce(
                      (acc, e) => acc + (Number(e.debit) || 0),
                      0,
                    ),
                  ).toFixed(2)}
                </td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </section>
  {:else if currentTab === 'bank-feed'}
    <div class="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div class="bg-slate-900/50 border border-slate-800 rounded-[2.5rem] p-10 flex flex-col items-center justify-center text-center space-y-6">
          <div class="w-24 h-24 bg-blue-500/10 rounded-full flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <div>
            <h2 class="text-3xl font-black text-white">{unreconciledCount} Pending Transactons</h2>
            <p class="text-slate-500 mt-2 max-w-sm">Imported bank data waiting to be categorized and posted to your ledger.</p>
          </div>
          <button 
            onclick={() => showImportCenter = true}
            class="px-10 py-4 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl shadow-xl shadow-blue-500/20 transition-all flex items-center gap-3 active:scale-95"
          >
            Open Reconciliation Center
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>

        <div class="bg-slate-900/30 border border-slate-800/50 rounded-[2.5rem] p-10 space-y-8">
          <h3 class="text-xl font-bold text-slate-300">How it works</h3>
          <div class="space-y-6">
            <div class="flex gap-4">
              <div class="w-10 h-10 bg-slate-800 rounded-xl flex items-center justify-center font-black text-blue-400 shrink-0">1</div>
              <div>
                <h4 class="font-bold text-white">Import Statements</h4>
                <p class="text-sm text-slate-500">Upload CSV files from your bank using the mapper.</p>
              </div>
            </div>
            <div class="flex gap-4">
              <div class="w-10 h-10 bg-slate-800 rounded-xl flex items-center justify-center font-black text-blue-400 shrink-0">2</div>
              <div>
                <h4 class="font-bold text-white">Review & Categorize</h4>
                <p class="text-sm text-slate-500">Our engine suggests categories. You review and verify them.</p>
              </div>
            </div>
            <div class="flex gap-4">
              <div class="w-10 h-10 bg-slate-800 rounded-xl flex items-center justify-center font-black text-blue-400 shrink-0">3</div>
              <div>
                <h4 class="font-bold text-white">Post to Ledger</h4>
                <p class="text-sm text-slate-500">Confirmed transactions are added to your history and update balances.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {#if unreconciledCount === 0}
        <div class="bg-emerald-500/5 border border-emerald-500/10 p-20 rounded-[3rem] flex flex-col items-center justify-center text-center">
          <div class="w-20 h-20 bg-emerald-500/10 rounded-full flex items-center justify-center text-emerald-400 mb-6">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 class="text-2xl font-black text-emerald-400">All Caught Up!</h3>
          <p class="text-slate-500 mt-2">Zero pending transactions. Your finances are perfectly reconciled.</p>
        </div>
      {/if}
    </div>
  {:else if currentTab === 'budgets'}
    <section class="space-y-6 animate-in slide-in-from-bottom-4 duration-500 pb-20">
      <div class="flex flex-col md:flex-row justify-between items-center bg-slate-900 shadow-2xl p-6 rounded-3xl border border-slate-800 gap-6">
        <div>
          <h3 class="text-xl font-bold">Monthly Budgets</h3>
          <p class="text-slate-500 text-sm">Target vs. Actual spending for your household.</p>
        </div>
        <div class="flex gap-4 items-center bg-slate-950 p-2 rounded-2xl border border-slate-800">
          <div class="flex gap-2 items-center px-4">
            <input type="number" bind:value={newBudgetMonth} min="1" max="12" class="w-8 bg-transparent text-center font-bold text-lg outline-none text-blue-400" />
            <span class="text-slate-600 font-bold">/</span>
            <input type="number" bind:value={newBudgetYear} class="w-16 bg-transparent text-center font-bold text-lg outline-none text-blue-400" />
          </div>
          <button 
            onclick={handleCreateBudget}
            class="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl transition-all shadow-lg shadow-blue-900/40 active:scale-95"
          >
            Create Budget
          </button>
        </div>
      </div>

      {#if budgets.length === 0}
        <div class="py-24 text-center bg-slate-900/30 rounded-3xl border border-dashed border-slate-800">
          <div class="bg-slate-800 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 class="text-xl font-bold text-slate-300">Set Your First Target</h3>
          <p class="text-slate-500 mt-2 max-w-sm mx-auto">Budgets help you stay on track by comparing monthly limits against real transaction data.</p>
        </div>
      {:else}
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {#each budgets as b}
            <div class="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl flex flex-col">
              <div class="p-6 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
                <div class="flex items-center gap-4">
                  <div class="bg-blue-600/20 px-4 py-2 rounded-2xl border border-blue-500/20 text-center min-w-[60px]">
                    <span class="text-blue-400 font-black text-2xl block leading-none">{b.month}</span>
                    <span class="text-[9px] text-blue-500 uppercase font-black tracking-widest leading-none">MONTH</span>
                  </div>
                  <div>
                    <h4 class="text-xl font-bold text-white leading-tight">{b.name}</h4>
                    <span class="text-[10px] text-slate-500 font-black uppercase tracking-widest">{b.year}</span>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <button 
                    onclick={() => { activeBudgetId = b.id; showAddBudgetLine = true; }}
                    class="p-3 bg-slate-800 hover:bg-blue-600 text-slate-400 hover:text-white rounded-2xl transition-all shadow-xl"
                    title="Add Category"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clip-rule="evenodd" />
                    </svg>
                  </button>
                  <button 
                    onclick={() => handleDeleteBudget(b.id)}
                    class="p-3 bg-slate-800 hover:bg-red-600/20 hover:text-red-500 text-slate-500 rounded-2xl transition-all shadow-xl"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>

              <div class="p-6 flex-1 space-y-6">
                {#if budgetVariances[b.id]}
                  <div class="grid grid-cols-2 gap-4 mb-2">
                    <div class="bg-slate-950/50 p-4 rounded-2xl border border-slate-800">
                      <p class="text-[10px] text-slate-500 font-black uppercase tracking-widest mb-1">Total Planned</p>
                      <p class="text-xl font-mono font-bold text-white">${budgetVariances[b.id].total_planned.toFixed(2)}</p>
                    </div>
                    <div class="bg-slate-950/50 p-4 rounded-2xl border border-slate-800">
                      <p class="text-[10px] text-slate-500 font-black uppercase tracking-widest mb-1">Total Actual</p>
                      <p class="text-xl font-mono font-bold {budgetVariances[b.id].total_actual > budgetVariances[b.id].total_planned ? 'text-rose-500' : 'text-emerald-500'}">${budgetVariances[b.id].total_actual.toFixed(2)}</p>
                    </div>
                  </div>

                  <div class="space-y-5">
                    {#each budgetVariances[b.id].lines as line}
                      {@const progress = Math.min((Number(line.actual) / Number(line.planned)) * 100, 100)}
                      {@const isOver = Number(line.actual) > Number(line.planned)}
                      <div class="group">
                        <div class="flex justify-between items-end mb-2">
                          <div>
                            <span class="text-sm font-bold text-slate-200 block">{line.account_name}</span>
                            <span class="text-[10px] text-slate-500 font-black uppercase">{((Number(line.actual) / Number(line.planned)) * 100).toFixed(0)}% Utilized</span>
                          </div>
                          <div class="text-right">
                            <p class="text-sm font-mono font-bold {isOver ? 'text-rose-500' : 'text-blue-400'}">
                              ${Number(line.actual).toFixed(2)} 
                              <span class="text-slate-600 font-normal">/ ${Number(line.planned).toFixed(2)}</span>
                            </p>
                          </div>
                        </div>
                        <div class="h-3 bg-slate-950 rounded-full border border-slate-800 overflow-hidden shadow-inner p-0.5">
                          <div 
                            class="h-full rounded-full transition-all duration-1000 shadow-lg {isOver ? 'bg-gradient-to-r from-rose-600 to-rose-400' : 'bg-gradient-to-r from-blue-600 to-blue-400'}" 
                            style="width: {progress}%"
                          ></div>
                        </div>
                      </div>
                    {/each}

                    {#if budgetVariances[b.id].lines.length === 0}
                      <div class="py-12 flex flex-col items-center justify-center text-slate-600 gap-3 border-2 border-dashed border-slate-800 rounded-3xl">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                        <p class="text-sm italic">Click the (+) button above to set categories.</p>
                      </div>
                    {/if}
                  </div>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </section>
  {:else if currentTab === 'rules'}
    <section class="space-y-6 animate-in slide-in-from-bottom-4 duration-500 pb-20">
      <div class="flex flex-col md:flex-row justify-between items-center bg-slate-900 shadow-2xl p-6 rounded-3xl border border-slate-800 gap-6">
        <div>
          <h3 class="text-xl font-bold">Automated Rules</h3>
          <p class="text-slate-500 text-sm">Categorize transactions automatically based on merchant names.</p>
        </div>
        <button 
          onclick={() => showAddRule = true}
          class="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl transition-all shadow-lg shadow-blue-900/40 active:scale-95"
        >
          Create Rule
        </button>
      </div>

      {#if rules.length === 0}
        <div class="py-24 text-center bg-slate-900/30 rounded-3xl border border-dashed border-slate-800">
          <div class="bg-slate-800 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </div>
          <h3 class="text-xl font-bold text-slate-300">Automation Awaits</h3>
          <p class="text-slate-500 mt-2 max-w-sm mx-auto">Rules help you save time by automatically assigning categories to recurring transactions.</p>
        </div>
      {:else}
        <div class="grid grid-cols-1 gap-4">
          {#each rules as rule}
            <div class="bg-slate-900 border border-slate-800 p-6 rounded-3xl flex justify-between items-center group transition-all hover:border-slate-700 shadow-xl">
              <div class="flex items-center gap-6">
                <div class="flex flex-col items-center justify-center bg-slate-950 w-12 h-12 rounded-2xl border border-slate-800 group-hover:border-blue-500/30 transition-colors">
                  <span class="text-[10px] text-slate-500 font-black uppercase leading-none mb-1">PRI</span>
                  <span class="text-lg font-black text-blue-400 leading-none">{rule.priority}</span>
                </div>
                <div>
                  <div class="flex items-center gap-2 mb-1">
                    <span class="text-xs font-black text-slate-500 uppercase tracking-widest">When Merchant contains</span>
                    <span class="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-sm font-bold rounded-lg border border-blue-500/20">{rule.condition_json.merchant_contains}</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-black text-slate-500 uppercase tracking-widest">Then Assign</span>
                    <span class="text-white font-bold">{accounts.find(a => a.id === rule.action_json.assign_account_id)?.name || 'Unknown Account'}</span>
                  </div>
                </div>
              </div>

              <div class="flex items-center gap-4">
                <button 
                  onclick={() => toggleRule(rule)}
                  class="px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all {rule.active ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/30' : 'bg-slate-800 text-slate-500 border border-slate-700'}"
                >
                  {rule.active ? 'Active' : 'Paused'}
                </button>
                <button 
                  onclick={() => handleDeleteRule(rule.id)}
                  class="p-3 bg-slate-800 hover:bg-red-600/20 hover:text-red-500 text-slate-500 rounded-2xl transition-all"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </section>
  {/if}

  {#if showAddRule}
    <div class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[60] flex items-center justify-center p-4">
      <div class="bg-slate-900 border border-slate-800 rounded-[2.5rem] w-full max-w-lg shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        <div class="p-8 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
          <div>
            <h3 class="text-2xl font-black text-white px-1">Create Rule</h3>
            <p class="text-slate-500 text-sm">Automate your categorization.</p>
          </div>
          <button onclick={() => showAddRule = false} class="p-3 bg-slate-800 hover:bg-slate-700 rounded-2xl transition-colors text-slate-400 active:scale-90">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="p-8 space-y-8">
          <div class="space-y-3">
            <label class="text-xs font-black text-slate-500 uppercase tracking-widest ml-1">Condition: Merchant Name</label>
            <input 
              type="text" 
              bind:value={newRuleMerchant} 
              placeholder="e.g. Starbucks"
              class="w-full px-6 py-4 bg-slate-950 border border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 outline-none text-xl font-bold transition-all text-white placeholder:text-slate-800 shadow-inner" 
            />
          </div>

          <div class="space-y-3">
            <label class="text-xs font-black text-slate-500 uppercase tracking-widest ml-1">Action: Assign To Account</label>
            <div class="relative group">
              <select 
                bind:value={newRuleAccountId}
                class="w-full pl-6 pr-12 py-5 bg-slate-950 border border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 outline-none text-lg font-bold transition-all appearance-none text-white shadow-inner"
              >
                <option value={null}>Select account...</option>
                {#each accounts.filter(a => a.type === 'expense') as acc}
                  <option value={acc.id}>{acc.name}</option>
                {/each}
              </select>
              <div class="absolute right-6 top-1/2 -translate-y-1/2 pointer-events-none text-slate-600">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
              </div>
            </div>
          </div>

          <div class="space-y-3">
            <label class="text-xs font-black text-slate-500 uppercase tracking-widest ml-1">Priority (Higher runs first)</label>
            <input 
              type="number" 
              bind:value={newRulePriority} 
              class="w-full px-6 py-4 bg-slate-950 border border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 outline-none text-xl font-bold transition-all text-white shadow-inner" 
            />
          </div>

          <button 
            onclick={handleCreateRule}
            disabled={!newRuleMerchant || !newRuleAccountId}
            class="w-full py-6 bg-blue-600 hover:bg-blue-500 disabled:opacity-30 disabled:grayscale text-white text-xl font-black rounded-3xl transition-all shadow-2xl shadow-blue-500/20 active:scale-95"
          >
            Save Rule
          </button>
        </div>
      </div>
    </div>
  {/if}


  {#if showAddBudgetLine}
    <div class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[60] flex items-center justify-center p-4">
      <div class="bg-slate-900 border border-slate-800 rounded-[2.5rem] w-full max-w-lg shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        <div class="p-8 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
          <div>
            <h3 class="text-2xl font-black text-white px-1">Add Category</h3>
            <p class="text-slate-500 text-sm">Select an expense category to track.</p>
          </div>
          <button onclick={() => showAddBudgetLine = false} class="p-3 bg-slate-800 hover:bg-slate-700 rounded-2xl transition-colors text-slate-400 active:scale-90">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="p-8 space-y-8">
          <div class="space-y-3">
            <label class="text-xs font-black text-slate-500 uppercase tracking-widest ml-1">Expense Account</label>
            <div class="relative group">
              <select 
                bind:value={newBudgetLineAccountId}
                class="w-full pl-6 pr-12 py-5 bg-slate-950 border border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 outline-none text-lg font-bold transition-all appearance-none text-white shadow-inner"
              >
                <option value={null}>Select category...</option>
                {#each accounts.filter(a => a.type === 'expense') as acc}
                  <option value={acc.id}>{acc.name}</option>
                {/each}
              </select>
              <div class="absolute right-6 top-1/2 -translate-y-1/2 pointer-events-none text-slate-600">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
              </div>
            </div>
          </div>

          <div class="space-y-3">
            <label class="text-xs font-black text-slate-500 uppercase tracking-widest ml-1">Monthly Spending Limit</label>
            <div class="relative group">
              <span class="absolute left-6 top-1/2 -translate-y-1/2 text-2xl font-black text-blue-500">$</span>
              <input 
                type="number" 
                bind:value={newBudgetLineAmount} 
                step="50"
                placeholder="0.00"
                class="w-full pl-12 pr-6 py-5 bg-slate-950 border border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 outline-none text-4xl font-black transition-all text-white placeholder:text-slate-800 shadow-inner" 
              />
            </div>
          </div>

          <button 
            onclick={handleAddBudgetLine}
            disabled={!newBudgetLineAccountId}
            class="w-full py-6 bg-blue-600 hover:bg-blue-500 disabled:opacity-30 disabled:grayscale text-white text-xl font-black rounded-3xl transition-all shadow-2xl shadow-blue-500/20 active:scale-95"
          >
            Add to Monthly Budget
          </button>
        </div>
      </div>
    </div>
  {/if}

  {#if showSettings}
    <div
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto"
    >
      <div
        class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-md shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200"
      >
        <div
          class="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50"
        >
          <h3 class="text-xl font-bold">Settings</h3>
          <button
            onclick={() => (showSettings = false)}
            aria-label="Close"
            class="p-2 hover:bg-slate-800 rounded-xl transition-colors text-slate-400"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              /></svg
            >
          </button>
        </div>
        <div class="p-8 space-y-6">
          <div>
            <label
              for="default-currency"
              class="block text-xs font-bold text-slate-500 uppercase mb-2"
              >Default Currency</label
            >
            <select
              id="default-currency"
              bind:value={defaultCurrency}
              onchange={() =>
                localStorage.setItem("defaultCurrency", defaultCurrency)}
              class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-blue-500 transition-colors"
            >
              <option value="CAD">CAD (Canadian Dollar)</option>
              <option value="USD">USD (US Dollar)</option>
              <option value="EUR">EUR (Euro)</option>
              <option value="GBP">GBP (British Pound)</option>
            </select>
            <p class="text-[10px] text-slate-600 mt-2 italic">
              New accounts will default to this selection.
            </p>
          </div>

          <!-- Household Settings inline -->
          <div class="pt-6 border-t border-slate-800">
            <h4 class="text-sm font-bold text-blue-400 mb-4">{household?.name || "Your Household"}</h4>
            {#if household && household.members}
              <div class="space-y-2 mb-6">
                {#each household.members as member}
                  <div class="flex justify-between items-center bg-slate-950 px-4 py-2 rounded-xl border border-slate-800">
                    <div>
                      <span class="text-slate-300 text-sm block">{member.email}</span>
                      <div class="flex items-center gap-2">
                        <span class="text-[10px] text-slate-500 uppercase tracking-widest">{member.role}</span>
                        {#if member.status === 'pending'}
                          <span class="text-[8px] bg-amber-500/10 text-amber-500 px-1.5 py-0.5 rounded-full font-black uppercase tracking-widest border border-amber-500/20">Invited</span>
                        {/if}
                      </div>
                    </div>
                    <button onclick={() => handleRemoveMember(member.user_id)} aria-label="Remove member" class="text-rose-500 hover:text-rose-400 p-1 bg-rose-500/10 rounded">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                  </div>
                {/each}
              </div>
            {/if}

            <form onsubmit={(e) => { e.preventDefault(); handleInviteMember(); }} class="flex flex-col gap-3">
              <label for="invite-email" class="block text-xs font-bold text-slate-500 uppercase">Invite Member by Email</label>
              <div class="flex flex-col sm:flex-row gap-2">
                <input id="invite-email" type="email" bind:value={inviteEmail} required disabled={isInviting} placeholder="partner@email.com" class="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500" />
                <select bind:value={inviteRole} disabled={isInviting} class="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500">
                  <option value="owner">Owner</option>
                  <option value="member">Member</option>
                  <option value="read_only">Read-Only</option>
                </select>
                <button type="submit" disabled={isInviting} class="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-sm font-bold transition-all whitespace-nowrap">
                  {isInviting ? 'Sending...' : 'Invite'}
                </button>
              </div>
            </form>
          </div>
        </div>
        <div class="p-8 bg-slate-900 border-t border-slate-800">
          <button
            onclick={() => (showSettings = false)}
            class="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl shadow-lg shadow-blue-500/20 transition-all"
          >
            Save & Close
          </button>
        </div>
      </div>
    </div>
  {/if}

  <ImportCenter 
    bind:isOpen={showImportCenter} 
    {accounts}
    onimported={refreshData}
  />
</div>

<style>
  .bg-checkered {
    background-image: radial-gradient(#1e293b 1px, transparent 1px);
    background-size: 20px 20px;
  }
  .custom-scrollbar::-webkit-scrollbar {
    width: 5px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: #0f172a;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: #1e293b;
    border-radius: 10px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #334155;
  }
</style>
