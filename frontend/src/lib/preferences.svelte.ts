// Per-browser preferences, shared by every page. Saved in localStorage, so they
// apply to this browser only (not to the account).

export const CURRENCIES = [
    { code: 'CAD', label: 'CAD (Canadian Dollar)' },
    { code: 'USD', label: 'USD (US Dollar)' },
    { code: 'EUR', label: 'EUR (Euro)' },
    { code: 'GBP', label: 'GBP (British Pound)' },
] as const;

const CURRENCY_KEY = 'defaultCurrency';
const FALLBACK_CURRENCY = 'CAD';

function readStored(key: string): string | null {
    try {
        return localStorage.getItem(key);
    } catch {
        // No localStorage (prerendering) or blocked by the browser.
        return null;
    }
}

function writeStored(key: string, value: string) {
    try {
        localStorage.setItem(key, value);
    } catch {
        // Blocked by the browser; the preference lasts for this page load only.
    }
}

class Preferences {
    #currency = $state(readStored(CURRENCY_KEY) ?? FALLBACK_CURRENCY);

    /** Currency that new accounts start with. */
    get defaultCurrency(): string {
        return this.#currency;
    }

    set defaultCurrency(code: string) {
        this.#currency = code;
        writeStored(CURRENCY_KEY, code);
    }
}

export const preferences = new Preferences();
