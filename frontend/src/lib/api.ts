export const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1';

export async function request(path: string, options: RequestInit = {}) {
    const token = localStorage.getItem('token');

    const headers = new Headers(options.headers);
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(`${BASE_URL}${path}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        localStorage.removeItem('token');
        // In a real app, redirect to login
    }

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || 'Request failed');
    }

    return response.json();
}

export const api = {
    get: (path: string) => request(path, { method: 'GET' }),
    post: (path: string, body: any) => request(path, { method: 'POST', body: JSON.stringify(body) }),
    postForm: (path: string, formData: FormData) => request(path, { method: 'POST', body: formData }),
    put: (path: string, body: any) => request(path, { method: 'PUT', body: JSON.stringify(body) }),
    patch: (path: string, body: any) => request(path, { method: 'PATCH', body: JSON.stringify(body) }),
    delete: (path: string) => request(path, { method: 'DELETE' }),
};
