// In development the Vite dev server (port 5173) talks to the backend on port 8000.
// Production builds are served by the backend itself, so use a same-origin path;
// a hard-coded localhost would only work in a browser on the server machine.
export const BASE_URL =
    import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? 'http://localhost:8000/api/v1' : '/api/v1');

let unauthorizedHandler: (() => void) | null = null;

/** Called whenever the API rejects the stored login (HTTP 401). Set by the session. */
export function setUnauthorizedHandler(handler: () => void) {
    unauthorizedHandler = handler;
}

export function getToken(): string | null {
    try {
        return localStorage.getItem('token');
    } catch {
        return null;
    }
}

/** Turn a FastAPI error body into a readable message. */
function describeError(body: any, status: number): string {
    const detail = body?.detail;
    if (typeof detail === 'string') return detail;
    // Validation errors (422) arrive as a list of {loc, msg} objects.
    if (Array.isArray(detail) && detail.length) {
        return detail.map((d) => d?.msg ?? String(d)).join('; ');
    }
    return `Request failed (HTTP ${status})`;
}

export async function request<T = any>(path: string, options: RequestInit = {}): Promise<T> {
    const token = getToken();

    const headers = new Headers(options.headers);
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
    }

    let response: Response;
    try {
        response = await fetch(`${BASE_URL}${path}`, { ...options, headers });
    } catch {
        throw new Error('Could not reach the Hearth server. Check your connection and try again.');
    }

    if (response.status === 401 && token) {
        unauthorizedHandler?.();
    }

    // Some endpoints answer with an empty body (e.g. 204 No Content).
    const text = await response.text();
    let body: any = null;
    if (text) {
        try {
            body = JSON.parse(text);
        } catch {
            body = null;
        }
    }

    if (!response.ok) {
        throw new Error(describeError(body, response.status));
    }

    return body as T;
}

export const api = {
    get: (path: string) => request(path, { method: 'GET' }),
    post: (path: string, body: any) => request(path, { method: 'POST', body: JSON.stringify(body) }),
    postForm: (path: string, formData: FormData) => request(path, { method: 'POST', body: formData }),
    put: (path: string, body: any) => request(path, { method: 'PUT', body: JSON.stringify(body) }),
    patch: (path: string, body: any) => request(path, { method: 'PATCH', body: JSON.stringify(body) }),
    delete: (path: string) => request(path, { method: 'DELETE' }),
};
