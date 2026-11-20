// In-app notifications ("toasts"), shown by <Toaster /> in the root layout.
// Use these instead of window.alert(), which blocks the page and can't be styled.

export type ToastKind = 'success' | 'error' | 'info';

export interface Toast {
    id: number;
    kind: ToastKind;
    message: string;
}

const DURATION_MS: Record<ToastKind, number> = {
    success: 4000,
    info: 6000,
    error: 9000,
};

class Notifier {
    toasts = $state<Toast[]>([]);
    #nextId = 1;

    #push(kind: ToastKind, message: string): number {
        const id = this.#nextId++;
        this.toasts = [...this.toasts, { id, kind, message }];
        setTimeout(() => this.dismiss(id), DURATION_MS[kind]);
        return id;
    }

    success = (message: string) => this.#push('success', message);
    info = (message: string) => this.#push('info', message);
    error = (message: string) => this.#push('error', message);

    dismiss = (id: number) => {
        this.toasts = this.toasts.filter((t) => t.id !== id);
    };
}

export const notify = new Notifier();

/** A readable message from anything that was thrown. */
export function errorMessage(e: unknown): string {
    if (e instanceof Error) return e.message;
    if (typeof e === 'string') return e;
    return 'Something went wrong.';
}
