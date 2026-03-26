import { api } from "./api";

export class Session {
    user = $state<any>(null);
    loading = $state(true);

    async init() {
        if (typeof localStorage === 'undefined') return;
        const token = localStorage.getItem('token');
        if (!token) {
            this.loading = false;
            return;
        }

        try {
            this.user = await api.get('/auth/me');
        } catch (e) {
            console.error("Failed to fetch user", e);
            localStorage.removeItem('token');
        } finally {
            this.loading = false;
        }
    }

    logout() {
        localStorage.removeItem('token');
        this.user = null;
        window.location.href = '/login';
    }
}

export const session = new Session();
