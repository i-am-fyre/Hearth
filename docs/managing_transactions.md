# Managing Accounts & Transactions

While automated imports and AI receipt parsing are powerful, understanding how to manually manage your accounts and transactions forms the underlying foundation of Hearth.

## Accounts

Because Hearth uses [Double-Entry Bookkeeping](accounting_terms.md), money must always flow between accounts.

### 1. Account Types
When you create an account, you must assign it one of four types:
- **Asset**: Things you own (Checking, Savings, Cash).
- **Liability**: Things you owe (Credit Cards, Loans).
- **Income**: Sources of money (Salary, Interest).
- **Expense**: Where your money goes (Groceries, Rent, Utilities).

### 2. Creating an Account
You can create accounts by navigating to the **Accounts** page via the sidebar. You can also create an account *inline* while adding a transaction or importing a CSV feed if you realize you miss a specific category.

## Transactions

A transaction records the movement of money from one account to another on a specific date. 

### Adding a Manual Transaction
1. Click the **+ Transaction** button in the dashboard or ledger view.
2. Enter the **Date**, **Amount**, and **Description**.
3. Select the **From Account** (Target / Credit) and the **To Account** (Destination / Debit). 
   - *Example: Buying $50 of groceries means money leaves "Checking" (From) and goes to "Groceries" (To).*
4. Click **Save Transaction**. Hearth automatically creates the balancing double-entries behind the scenes.

### Viewing and Editing
Click on any transaction row in your ledger to open its **Detail Modal**. 
- Here you can see the split debits and credits.
- Click **Edit Mode** (the pencil icon) to change the date, description, or accounts.
- Click **Attach Receipt** to upload documentation to the existing transaction.

## Split Entries

Sometimes a single real-world purchase involves multiple categories. For example, a $100 receipt from a superstore might include $70 for Groceries and $30 for Clothing.

Hearth supports **Split Transactions**:

1. Open the Transaction Detail Modal and click **Edit Mode**.
2. Under the specific entry (e.g., the $100 pointing to Groceries), click the **Split** button.
3. This divides the entry into two zero-dollar entries.
4. Adjust the amounts (e.g., $70 and $30) and select the correct destination accounts for each.
5. Save the transaction. As long as the total debits still equal the total credits, Hearth will accept the split.

*Note: The AI Receipt parser automatically attempts to map line items into split entries during verification.*
