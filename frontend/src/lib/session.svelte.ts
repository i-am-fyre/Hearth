import { goto } from '$app/navigation';
import { api, getToken, setUnauthorizedHandler } from './api';
import { isPublicPath } from './routes';

function clearToken() {
    try {
        localStorage.removeItem('token');
    } catch {
        // Storage blocked; nothing to clear.
    }
}

export class Session {
    user = $state<any>(null);
    /** True until we know whether the stored login is valid. */
    loading = $state(true);
    #pending: Promise<void> | null = null;

    /** Load the signed-in user. Safe to call repeatedly; only one request is made. */
    init(): Promise<void> {
        this.#pending ??= this.#load();
        return this.#pending;
    }

    async #load() {
        if (typeof window === 'undefined') return;
        if (!getToken()) {
            this.user = null;
            this.loading = false;
            return;
        }
        try {
            this.user = await api.get('/auth/me');
        } catch (e) {
            console.warn('Stored login is no longer valid; signing out.', e);
            this.user = null;
            clearToken();
        } finally {
            this.loading = false;
        }
    }

    /** Store a new login token (from /auth/login) and load the user it belongs to. */
    async signIn(token: string) {
        localStorage.setItem('token', token);
        this.loading = true;
        this.#pending = null;
        await this.init();
    }

    logout() {
        clearToken();
        this.user = null;
        // A full reload drops any data the previous user had loaded.
        window.location.href = '/login';
    }

    /** The server rejected our token (expired, or the server's key changed). */
    handleUnauthorized() {
        clearToken();
        this.user = null;
        this.loading = false;
        this.#pending = null;
        if (!isPublicPath(window.location.pathname)) {
            goto('/login');
        }
    }
}

export const session = new Session();
setUnauthorizedHandler(() => session.handleUnauthorized());
