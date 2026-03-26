<script lang="ts">
  import { api } from '$lib/api';
  import { goto } from '$app/navigation';

  let email = '';
  let password = '';
  let confirmPassword = '';
  let error = '';
  let loading = false;

  async function handleRegister() {
    if (password !== confirmPassword) {
      error = "Passwords do not match";
      return;
    }
    
    loading = true;
    error = '';
    try {
      await api.post('/auth/register', { email, password });
      // Redirect to login after successful registration
      goto('/login');
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
      <h1 class="text-3xl font-bold bg-gradient-to-r from-green-400 to-blue-500 bg-clip-text text-transparent">
        Join Hearth
      </h1>
      <p class="text-slate-400 mt-2">Create your privacy-first account</p>
    </div>

    <form onsubmit={handleRegister} class="space-y-6">
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
        <label for="password" class="block text-sm font-medium text-slate-300 mb-1">Password</label>
        <input
          type="password"
          id="password"
          bind:value={password}
          required
          class="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
          placeholder="Min 8 characters"
        />
      </div>

      <div>
        <label for="confirm" class="block text-sm font-medium text-slate-300 mb-1">Confirm Password</label>
        <input
          type="password"
          id="confirm"
          bind:value={confirmPassword}
          required
          class="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
          placeholder="••••••••"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        class="w-full py-3 px-4 bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-500 hover:to-blue-500 text-white font-semibold rounded-lg shadow-lg transform transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Creating account...' : 'Create Account'}
      </button>
    </form>

    <div class="mt-8 pt-6 border-t border-slate-800 text-center text-sm text-slate-400">
      Already have an account? <a href="/login" class="text-blue-400 hover:text-blue-300 font-medium">Sign in</a>
    </div>
  </div>
</div>
