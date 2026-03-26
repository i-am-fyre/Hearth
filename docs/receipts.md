# Receipts & AI Parsing

Hearth includes an advanced receipt management system with AI-powered data extraction, duplicate detection, and a dedicated Receipt Center for reviewing and linking receipts to your ledger.

## Uploading Receipts

You can upload receipt images directly from the dashboard:

- **Single Upload**: Click the receipt icon on any unmatched bank transaction.
- **Batch Upload**: Use the **Batch Upload** button in the header to upload multiple receipts at once. Processing happens in the background — come back to the Receipt Center when done.

Supported formats: JPEG, PNG, WebP, PDF.

## Receipt Center

The **Receipt Center** (accessible from the dashboard toolbar) shows all receipts that haven't yet been linked to a transaction. For each receipt, you can:

- 👁️ **Preview** the receipt image.
- ✅ **Approve & Link** to a matching transaction (suggested matches are shown automatically).
- 🔄 **Reprocess** stuck receipts (stuck in *pending* or *failed* state) with the "Reprocess Stuck Receipts" button.
- 🗑️ **Delete** the receipt if it's a duplicate or incorrect upload.

## AI-Powered Parsing (Gemini)

If a `GEMINI_API_KEY` is configured, Hearth uses **Google Gemini** to extract:

- **Merchant name**
- **Transaction date**
- **Total amount**
- **Line items** (individual products and prices)

Results are shown in the verification form with an **AI (Gemini)** extraction badge and a confidence score.

## OCR Fallback (Tesseract)

If no Gemini API key is configured — or if Gemini fails — Hearth falls back to **Tesseract OCR** for text extraction, followed by regex-based parsing to extract structured fields.

## Deduplication

Hearth computes a **SHA256 hash** of each uploaded file. If the same file is uploaded twice for the same account, the existing record is returned without creating a duplicate entry or re-running processing.

## Smart Transaction Matching

After AI/OCR processing, Hearth searches your existing transactions for potential matches based on:

- **Date** (±3 days window)
- **Amount** (within $0.05)
- **Merchant name** (fuzzy substring match)

Suggested matches appear in the Receipt Center so you can review and confirm with one click.

## Encryption & Privacy

Receipt files are **never stored in plain text**.

- Each receipt is encrypted using the user's unique **Fernet encryption key** before being saved to disk.
- Files are decrypted on-the-fly only when requested by an authenticated session.
- If the `backend/storage/` directory is backed up, files remain encrypted without the corresponding key.

---

*See [Configuration](configuration.md) to set up your Gemini API key.*
