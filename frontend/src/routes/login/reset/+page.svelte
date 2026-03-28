<script lang="ts">
    import { request } from '$lib/api';
    import { AlertTriangle, CheckCircle, Lock } from 'lucide-svelte';
    import { page } from '$app/stores';

    let token = $derived($page.url.searchParams.get('token') || '');
    let new_password = $state('');
    let confirm_password = $state('');
    let loading = $state(false);
    let success = $state(false);
    let error = $state('');

    async function handleReset() {
        if (new_password !== confirm_password) {
            error = "Passwords do not match.";
            return;
        }
        if (!token) {
            error = "Invalid or missing token. Please request a new password reset link.";
            return;
        }

        loading = true;
        error = '';
        try {
            await request('/auth/reset-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, new_password })
            });
            success = true;
        } catch (err: any) {
            error = err.message || 'The password reset token is invalid or has expired. Please try again.';
        } finally {
            loading = false;
        }
    }
</script>

<svelte:head>
    <title>Set New Password - Hearth</title>
</svelte:head>

<div class="flex flex-col items-center justify-center min-h-[80vh] px-4">
    <div class="w-full max-w-md p-8 bg-slate-900 rounded-2xl shadow-2xl border border-slate-800">
        <div class="text-center mb-8">
            <h1 class="text-3xl font-bold bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
                Hearth
            </h1>
            <p class="text-slate-400 mt-2 text-xl font-semibold">Set New Password</p>
        </div>

        {#if success}
            <div class="p-4 bg-green-500/10 border border-green-500/50 rounded-lg mb-6">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <CheckCircle class="h-5 w-5 text-green-400" />
                    </div>
                    <div class="ml-3">
                        <h3 class="text-sm font-medium text-green-400">
                            Password Reset Successful
                        </h3>
                        <div class="mt-2 text-sm text-green-500/80">
                            <p>Your password has been changed. You can now sign in with your new password.</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <a href="/login" class="w-full flex justify-center py-3 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold rounded-lg shadow-lg transform transition-all active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 focus:ring-blue-500">
                Sign in
            </a>
        {:else}
            <form onsubmit={(e) => { e.preventDefault(); handleReset(); }} class="space-y-6">
                {#if error}
                    <div class="p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-500 text-sm flex items-start gap-2">
                        <AlertTriangle class="h-5 w-5 shrink-0 mt-0.5" />
                        <span>{error}</span>
                    </div>
                {/if}

                <div>
                    <label for="new_password" class="block text-sm font-medium text-slate-300 mb-1">New Password</label>
                    <div class="relative">
                        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Lock class="h-5 w-5 text-slate-500" />
                        </div>
                        <input
                            type="password"
                            id="new_password"
                            bind:value={new_password}
                            required
                            class="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-white placeholder-slate-500"
                            placeholder="••••••••"
                        />
                    </div>
                </div>

                <div>
                    <label for="confirm_password" class="block text-sm font-medium text-slate-300 mb-1">Confirm Password</label>
                    <div class="relative">
                        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Lock class="h-5 w-5 text-slate-500" />
                        </div>
                        <input
                            type="password"
                            id="confirm_password"
                            bind:value={confirm_password}
                            required
                            class="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-white placeholder-slate-500"
                            placeholder="••••••••"
                        />
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={loading || !new_password || !confirm_password}
                    class="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold rounded-lg shadow-lg transform transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center"
                >
                    {#if loading}
                        <svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Resetting Password...
                    {:else}
                        Update Password
                    {/if}
                </button>
            </form>
        {/if}
    </div>
</div>
