// In-app confirm and prompt dialogs, shown by <DialogHost /> in the root layout.
// Use these instead of window.confirm() / window.prompt():
//
//   if (!(await confirmDialog({ title: 'Delete tag?', danger: true }))) return;
//   const name = await promptDialog({ title: 'Rule keyword', defaultValue: txn.description });

export interface ConfirmOptions {
    title: string;
    message?: string;
    confirmText?: string;
    cancelText?: string;
    /** Style the confirm button as destructive (red). */
    danger?: boolean;
}

export interface PromptOptions extends ConfirmOptions {
    defaultValue?: string;
    placeholder?: string;
}

interface ActiveDialog extends PromptOptions {
    kind: 'confirm' | 'prompt';
    value: string;
    resolve: (result: boolean | string | null) => void;
}

class DialogState {
    current = $state<ActiveDialog | null>(null);
    #queue: ActiveDialog[] = [];

    open(dialog: ActiveDialog) {
        if (this.current) this.#queue.push(dialog);
        else this.current = dialog;
    }

    /** Close the visible dialog. `accepted` is false when cancelled or dismissed. */
    close(accepted: boolean) {
        const dialog = this.current;
        if (!dialog) return;
        this.current = this.#queue.shift() ?? null;
        if (dialog.kind === 'confirm') dialog.resolve(accepted);
        else dialog.resolve(accepted ? dialog.value : null);
    }
}

export const dialogState = new DialogState();

/** Resolves to true if the user confirms, false if they cancel or dismiss. */
export function confirmDialog(options: ConfirmOptions): Promise<boolean> {
    return new Promise((resolve) =>
        dialogState.open({ kind: 'confirm', value: '', ...options, resolve: (r) => resolve(r === true) }),
    );
}

/** Resolves to the entered text, or null if the user cancels or dismisses. */
export function promptDialog(options: PromptOptions): Promise<string | null> {
    return new Promise((resolve) =>
        dialogState.open({
            kind: 'prompt',
            value: options.defaultValue ?? '',
            ...options,
            resolve: (r) => resolve(typeof r === 'string' ? r : null),
        }),
    );
}
