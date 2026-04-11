<script>
    import { onMount } from 'svelte';
    
    let status = { database_connected: false, is_writable: false };
    let dbUrl = "postgresql://hearth:postgres@localhost:5432/hearth";
    let message = "";
    let error = "";
    let testing = false;
    let saving = false;
    let success = false;

    async function checkStatus() {
        try {
            const res = await fetch('/api/v1/setup/status');
            status = await res.json();
        } catch (e) {
            console.error(e);
        }
    }

    async function testConnection() {
        testing = true;
        error = "";
        message = "";
        try {
            const res = await fetch('/api/v1/setup/test-db', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ database_url: dbUrl })
            });
            const data = await res.json();
            if (data.success) {
                message = "Connection successful!";
            } else {
                error = data.message;
            }
        } catch (e) {
            error = "Failed to communicate with setup API.";
        } finally {
            testing = false;
        }
    }

    async function saveConfig() {
        saving = true;
        error = "";
        message = "";
        try {
            const res = await fetch('/api/v1/setup/save-config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ database_url: dbUrl })
            });
            const data = await res.json();
            if (res.ok) {
                success = true;
                message = data.message;
                // Auto-restart after 2 seconds
                setTimeout(restartApp, 2000);
            } else {
                error = data.detail || "Failed to save configuration.";
            }
        } catch (e) {
            error = "Failed to communicate with setup API.";
        } finally {
            saving = false;
        }
    }

    async function restartApp() {
        try {
            await fetch('/api/v1/setup/restart', { method: 'POST' });
            message = "Restarting... Please refresh in 5-10 seconds.";
        } catch (e) {
            console.error(e);
        }
    }

    onMount(checkStatus);
</script>

<div class="setup-container">
    <div class="setup-card">
        <header>
            <div class="logo">Hearth</div>
            <h1>Welcome to Hearth</h1>
            <p>It looks like we need to finish setting up your database connection.</p>
        </header>

        {#if success}
            <div class="success-view">
                <div class="icon-check">✓</div>
                <h2>Configuration Saved!</h2>
                <p>{message}</p>
                <button on:click={() => window.location.href = '/'}>Go to Login</button>
            </div>
        {:else}
            <section class="status-section">
                <div class="status-badge {status.database_connected ? 'connected' : 'disconnected'}">
                    Database: {status.database_connected ? 'Connected' : 'Not Connected'}
                </div>
                {#if !status.is_writable}
                    <div class="alert warn">
                        <strong>Warning:</strong> The configuration file at <code>/etc/hearth/hearth.conf</code> is not writable by the application. You may need to run <code>sudo chown hearth:hearth /etc/hearth/hearth.conf</code> manually.
                    </div>
                {/if}
            </section>

            <section class="config-section">
                <label for="db-url">Database Connection URL</label>
                <input 
                    type="text" 
                    id="db-url" 
                    bind:value={dbUrl} 
                    placeholder="postgresql://user:password@host:port/dbname"
                />
                <p class="help">Example: <code>postgresql://hearth:postgres@localhost:5432/hearth</code></p>
            </section>

            {#if error}
                <div class="error-box">
                    <strong>Error:</strong> {error}
                </div>
            {/if}

            {#if message}
                <div class="message-box">
                    {message}
                </div>
            {/if}

            <div class="actions">
                <button class="secondary" on:click={testConnection} disabled={testing || saving}>
                    {testing ? 'Testing...' : 'Test Connection'}
                </button>
                <button class="primary" on:click={saveConfig} disabled={saving || testing}>
                    {saving ? 'Saving...' : 'Save & Start Hearth'}
                </button>
            </div>
        {/if}

        <footer>
            <p>Need help? Check the <a href="https://github.com/i-am-fyre/Hearth" target="_blank" rel="noopener noreferrer">documentation</a>.</p>
        </footer>
    </div>
</div>

<style>
    :global(body) {
        margin: 0;
        padding: 0;
        background: radial-gradient(circle at top right, #1a1a2e, #16213e);
        font-family: 'Inter', system-ui, sans-serif;
        color: white;
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .setup-container {
        width: 100%;
        max-width: 600px;
        padding: 2rem;
    }

    .setup-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 3rem;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }

    header {
        text-align: center;
        margin-bottom: 2.5rem;
    }

    .logo {
        font-size: 1.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }

    h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }

    header p {
        color: rgba(255, 255, 255, 0.6);
        margin-top: 0.5rem;
    }

    .status-section {
        margin-bottom: 2rem;
    }

    .status-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 99px;
        font-size: 0.875rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    .disconnected {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    .alert {
        padding: 1rem;
        border-radius: 12px;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    .warn {
        background: rgba(245, 158, 11, 0.1);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.2);
    }

    .config-section {
        margin-bottom: 2rem;
    }

    label {
        display: block;
        margin-bottom: 0.75rem;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.8);
    }

    input {
        width: 100%;
        box-sizing: border-box;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: white;
        font-family: inherit;
        font-size: 1rem;
    }

    input:focus {
        outline: none;
        border-color: #60a5fa;
        background: rgba(255, 255, 255, 0.1);
    }

    .help {
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.4);
        margin-top: 0.5rem;
    }

    .error-box {
        background: rgba(239, 68, 68, 0.1);
        color: #f87171;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        font-size: 0.9rem;
        word-break: break-all;
    }

    .message-box {
        background: rgba(16, 185, 129, 0.1);
        color: #34d399;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
    }

    .actions {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin-top: 2rem;
    }

    button {
        padding: 1rem;
        border-radius: 12px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        border: none;
    }

    .primary {
        background: #3b82f6;
        color: white;
    }

    .primary:hover:not(:disabled) {
        background: #2563eb;
        transform: translateY(-2px);
    }

    .secondary {
        background: rgba(255, 255, 255, 0.1);
        color: white;
    }

    .secondary:hover:not(:disabled) {
        background: rgba(255, 255, 255, 0.2);
    }

    button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    footer {
        margin-top: 3rem;
        text-align: center;
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.4);
    }

    footer a {
        color: #60a5fa;
        text-decoration: none;
    }

    .success-view {
        text-align: center;
        padding: 2rem 0;
    }

    .icon-check {
        width: 64px;
        height: 64px;
        background: #10b981;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        margin: 0 auto 1.5rem;
    }
</style>
