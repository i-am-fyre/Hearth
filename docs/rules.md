# Rules & Automation

Hearth features a powerful **Rules Engine** designed to automate the categorization and processing of imported transactions.

## How Rules Work

Rules consist of two main parts: **Conditions** and **Actions**. When a bank transaction is imported, the engine evaluates it against your active rules.

### Conditions
Conditions define the criteria that a transaction must meet. Examples include:
- `merchant_contains`: Matches if the merchant name includes a specific string (e.g., "WAL-MART").
- `amount_less_than`: Matches if the transaction amount is below a certain value.
- `amount_greater_than`: Matches if the transaction amount is above a certain value.

### Actions
Actions define what happens when a rule identifies a match. Common actions include:
- `assign_account_id`: Automatically maps the transaction to a specific Expense or Income account.
- `flag_for_review`: Marks the transaction for manual user intervention.

### Auto-Post
Individual rules can be configured with an **Auto-Post** flag. 
- If enabled, any transaction that matches the rule will be automatically "Posted" to the ledger without requiring manual confirmation.
- Common use cases include predictable monthly bills or recurring utility payments.

## Rule Priority

Rules are executed in order of their **Priority** (higher numbers first). This allows you to create broad "catch-all" rules with low priority and specific override rules with high priority.

> [!TIP]
> Use the "Dry Run" feature in the Rules UI to see how a new rule would have affected previously imported transactions before saving.
