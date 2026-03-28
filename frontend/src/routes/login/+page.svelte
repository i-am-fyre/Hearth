<script lang="ts">
  import { api } from '$lib/api';
  import { goto } from '$app/navigation';

  let email = '';
  let password = '';
  let error = '';
  let loading = false;

  async function handleLogin() {
    loading = true;
    error = '';
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);
      
      const data = await api.postForm('/auth/login', formData);
      localStorage.setItem('token', data.access_token);
      goto('/');
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }
</script>

<div class="flex flex-col items-center justify-center min-h-[80vh] px-4">
  <div class="w-full max-w-md p-8 bg-slate-900 rounded-2xl shadow-2xl border border-slate-800">
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
        Hearth
      </h1>
      <p class="text-slate-400 mt-2">Personal Finance for Your Household</p>
    </div>

    <form onsubmit={handleLogin} class="space-y-6">
      {#if error}
        <div class="p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-500 text-sm">
          {error}
        </div>
      {/if}

      <div>
        <label for="email" class="block text-sm font-medium text-slate-300 mb-1">Email Address</label>
        <input
          type="email"
          id="email"
          bind:value={email}
          required
          class="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
          placeholder="you@example.com"
        />
      </div>

      <div>
        <div class="flex justify-between items-center mb-1">
          <label for="password" class="block text-sm font-medium text-slate-300">Password</label>
          <div class="text-sm">
            <a href="/login/forgot" class="font-medium text-blue-400 hover:text-blue-300">
              Forgot your password?
            </a>
          </div>
        </div>
        <input
          type="password"
          id="password"
          bind:value={password}
          required
          class="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
          placeholder="••••••••"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        class="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold rounded-lg shadow-lg transform transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Signing in...' : 'Sign In'}
      </button>
    </form>

    <div class="mt-8 pt-6 border-t border-slate-800 text-center text-sm text-slate-400">
      Need an account? <a href="/register" class="text-blue-400 hover:text-blue-300 font-medium">Register here</a>
    </div>
  </div>
</div>
