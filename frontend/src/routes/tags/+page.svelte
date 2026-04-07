<script lang="ts">
    import { onMount } from 'svelte';
    import { request } from '$lib/api';
    import { Tag as TagIcon, Plus, Trash2, Edit2, Check, X } from 'lucide-svelte';
    import Navbar from '$lib/components/Navbar.svelte';

    type AppTag = {
        id: number;
        user_id: number;
        name: string;
        color_hex: string;
    };

    let tags = $state<AppTag[]>([]);
    let loading = $state(true);
    let error = $state<string | null>(null);

    // Form state
    let showForm = $state(false);
    let editingId = $state<number | null>(null);
    let tagName = $state('');
    let tagColor = $state('#3b82f6'); // Default blue

    async function loadTags() {
        loading = true;
        error = null;
        try {
            tags = await request<AppTag[]>('/tags');
        } catch (e: any) {
            error = e.message;
        } finally {
            loading = false;
        }
    }

    onMount(() => {
        loadTags();
    });

    async function handleSubmit(e: Event) {
        e.preventDefault();
        
        try {
            if (editingId) {
                const updated = await request<AppTag>(`/tags/${editingId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: tagName, color_hex: tagColor })
                });
                tags = tags.map(t => t.id === editingId ? updated : t);
            } else {
                const created = await request<AppTag>('/tags', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: tagName, color_hex: tagColor })
                });
                tags = [...tags, created];
            }
            resetForm();
        } catch (e: any) {
            alert(e.message);
        }
    }

    async function deleteTag(id: number) {
        if (!confirm('Are you sure you want to delete this tag? It will be removed from all associated transactions and entries.')) return;
        
        try {
            await request(`/tags/${id}`, { method: 'DELETE' });
            tags = tags.filter(t => t.id !== id);
        } catch (e: any) {
            alert(e.message);
        }
    }

    function editTag(tag: AppTag) {
        editingId = tag.id;
        tagName = tag.name;
        tagColor = tag.color_hex;
        showForm = true;
    }

    function resetForm() {
        showForm = false;
        editingId = null;
        tagName = '';
        tagColor = '#3b82f6';
    }
</script>

<svelte:head>
    <title>Tags - Hearth</title>
</svelte:head>

<Navbar />

<div class="p-8">
<div class="max-w-4xl mx-auto space-y-6">
    <div class="flex justify-between items-center bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-lg">
        <div>
            <h1 class="text-3xl font-bold bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent flex items-center gap-3">
                <TagIcon class="h-8 w-8 text-blue-400" />
                Tags & Categories
            </h1>
            <p class="text-slate-400 mt-2">Create custom categorizations for your transactions and individual splits.</p>
        </div>
        {#if !showForm}
            <button 
                class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium shadow-lg transition-all flex items-center gap-2"
                onclick={() => showForm = true}
            >
                <Plus class="h-5 w-5" />
                New Tag
            </button>
        {/if}
    </div>

    {#if showForm}
        <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-lg">
            <div class="flex items-center justify-between mb-6 border-b border-slate-800 pb-4">
                <h2 class="text-xl font-semibold text-white">
                    {editingId ? 'Edit Tag' : 'Create New Tag'}
                </h2>
                <button 
                    class="text-slate-400 hover:text-white transition-colors"
                    onclick={resetForm}
                >
                    <X class="h-6 w-6" />
                </button>
            </div>

            <form onsubmit={handleSubmit} class="space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-2">Tag Name</label>
                        <input
                            type="text"
                            bind:value={tagName}
                            required
                            placeholder="e.g. Groceries, Vacation"
                            class="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all font-medium"
                        />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-2">Custom Color</label>
                        <div class="flex items-center gap-4">
                            <input
                                type="color"
                                bind:value={tagColor}
                                required
                                class="h-12 w-16 p-1 bg-slate-800 border border-slate-700 rounded-lg cursor-pointer"
                            />
                            <div class="px-3 py-1.5 rounded-full text-sm font-medium flex items-center gap-1.5" style="background-color: {tagColor}20; color: {tagColor}; border: 1px solid {tagColor}40">
                                <TagIcon class="h-3 w-3" />
                                Preview
                            </div>
                        </div>
                    </div>
                </div>

                <div class="flex justify-end gap-3 pt-4 border-t border-slate-800">
                    <button
                        type="button"
                        class="px-5 py-2.5 rounded-lg font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
                        onclick={resetForm}
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={!tagName}
                        class="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white px-6 py-2.5 rounded-lg font-semibold shadow-lg transition-all disabled:opacity-50 flex items-center gap-2"
                    >
                        <Check class="h-5 w-5" />
                        {editingId ? 'Save Changes' : 'Create Tag'}
                    </button>
                </div>
            </form>
        </div>
    {/if}

    {#if loading}
        <div class="flex justify-center p-12">
            <div class="animate-spin h-8 w-8 text-blue-500">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
            </div>
        </div>
    {:else if error}
        <div class="bg-red-500/10 border border-red-500/50 text-red-500 p-6 rounded-2xl flex items-center gap-4">
            <X class="h-6 w-6 shrink-0" />
            <p>{error}</p>
        </div>
    {:else if tags.length === 0}
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center shadow-lg">
            <div class="mx-auto w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mb-4">
                <TagIcon class="h-8 w-8 text-slate-400" />
            </div>
            <h3 class="text-xl font-medium text-white">No tags created yet</h3>
            <p class="text-slate-400 mt-2 max-w-md mx-auto">Create your first tag to start categorizing your transactions and keeping your budget highly organized.</p>
        </div>
    {:else}
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {#each tags as tag (tag.id)}
                <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-600 transition-all group flex items-center justify-between shadow-lg">
                    <div class="flex items-center gap-3 overflow-hidden">
                        <div class="w-4 h-4 rounded-full flex-shrink-0" style="background-color: {tag.color_hex}"></div>
                        <span class="font-medium text-slate-200 truncate">{tag.name}</span>
                    </div>
                    <div class="flex items-center gap-1 opacity-100 md:opacity-0 group-hover:opacity-100 transition-opacity">
                        <button 
                            class="p-2 text-slate-400 hover:text-blue-400 hover:bg-slate-800 rounded-lg transition-colors"
                            onclick={() => editTag(tag)}
                        >
                            <Edit2 class="h-4 w-4" />
                        </button>
                        <button 
                            class="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
                            onclick={() => deleteTag(tag.id)}
                        >
                            <Trash2 class="h-4 w-4" />
                        </button>
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>
</div>
