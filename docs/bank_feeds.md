# Bank Feeds & CSV Import

Hearth allows you to import transactions directly from your financial institutions using CSV files. This speeds up your workflow by reducing manual data entry and ensuring accuracy.

## Importing Transactions

To begin importing, navigate to the **Import Center** in the sidebar.

### 1. Uploading a CSV
You can drag and drop your bank's CSV export into the upload zone. Hearth supports most bank formats through a flexible mapping system.

### 2. Column Mapping
Once a file is uploaded, you will see a preview of the data. You must map the columns from your CSV to Hearth's required fields:
- **Date**: The date the transaction occurred.
- **Description**: The merchant or transaction details.
- **Amount**: The transaction value.
    - If your bank provides separate **Debit** and **Credit** columns, you can map those instead of a single Amount column.

### 3. Rule Matching & Suggestions
As you import, the **Rules Engine** will automatically attempt to categorize your transactions based on your existing rules. 
- If a match is found, the transaction will be pre-filled with the suggested category.
- If no match is found, you can manually select a category during the reconciliation process.

## Reconciliation Center

After importing, transactions remain in a "Pending" state in the **Bank Feed** tab until they are reconciled.

### Matching Existing Transactions
Hearth automatically scans your ledger for existing manual entries that match the imported data (based on date, amount, and description).
- **Exact Match**: If an exact match is found, you can simply confirm the link.
- **Flagged**: If the amount and date match but the description is slightly different, it will be flagged for your review.

### Creating New Transactions
For transactions that don't yet exist in your ledger, you can create them directly from the Bank Feed. Simply select the appropriate target account, and Hearth will generate the double-entry records for you.

## Cleaning Up Feeds

### Bulk Discard
If you have imported old or duplicate data, you can use the **Discard All** feature to clear all unreconciled transactions from your feed.

### Individual Discard
You can also discard individual transactions by clicking the "Discard" button on any row in the Bank Feed list.

> [!TIP]
> Use the **Preview** feature before finalizing an import to ensure your column mapping is correct and avoid importing messy data.
