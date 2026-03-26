# API Reference

Hearth provides a powerful, RESTful API tailored and served by **FastAPI**.

Because it depends deeply on OpenAPI, you have access to interactive, automatically generated documentation the moment it is running locally.

## Viewing Interactive API Docs

Once your Hearth backend is running, the interactive API documentation can be accessed locally via two endpoints:

- **[Swagger UI](http://localhost:8000/docs)**: Navigate here for dynamic API exploration where you can execute requests directly from the UI.
- **[ReDoc](http://localhost:8000/redoc)**: An alternative renderer, best for sharing static and highly descriptive references.

## Key Endpoints

While the interactive docs are the source-of-truth, the following domains summarize the essential capabilities:

### Transactions
- **`GET /api/v1/transactions`**: List transactions in paginated form.
- **`POST /api/v1/transactions`**: Validate and post a new multiple-split transaction to the database safely.

### Accounts
- **`GET /api/v1/accounts`**: Retreive a hierarchical list of all created Assets, Liabilities, Income, and Expenses.
- **`POST /api/v1/accounts`**: Generate additional tracked categories or checking accounts dynamically.

### Rules Engine
Hearth possesses an integrated rules engine designed to streamline categorization of imported transactions automatically.
- **`GET /api/v1/rules`**: Returns existing automation scripts.
- **`POST /api/v1/rules`**: Establish regex and variable condition logic that triggers on future data.

### Bank Import
Manage external data ingestion and reconciliation.
- **`POST /api/v1/imports/csv`**: Upload a CSV file with custom column mapping.
- **`GET /api/v1/imports/unmatched`**: Retrieve imported transactions awaiting reconciliation.
- **`POST /api/v1/imports/reconcile`**: Link a bank transaction to an existing ledger entry or create a new one.
- **`DELETE /api/v1/imports/bulk`**: Discard all pending transactions in the feed.

### Receipts
Secure document management with OCR processing.
- **`POST /api/v1/receipts`**: Upload and encrypt a receipt; triggers the OCR and auto-creation pipeline.
- **`GET /api/v1/receipts/{id}/download`**: Decrypt and stream the original document.
- **`PATCH /api/v1/receipts/{id}/attach`**: Link a receipt to an existing transaction.

### Households
Manage shared access and family groups.
- **`GET /api/v1/households`**: Retrieve current household name and member list (including pending invites).
- **`POST /api/v1/households/invite`**: Invite a user by email; creates a pending invitation if the user is not yet registered.
- **`DELETE /api/v1/households/member/{user_id}`**: Remove a user from the household.

> [!TIP]
> The backend automatically validates parameters against defined Pydantic models. Refer to Swagger schemas to see exact constraints for creation payloads!
