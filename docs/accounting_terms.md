# Accounting Terms

Hearth leverages standard **double-entry bookkeeping** principles to manage finances. This system ensures your accounts always balance and provides tracking mechanisms that simple income/expense trackers lack.

## Core Financial Concepts

Here are definitions for the most common accounting terminology you'll encounter in Hearth:

### Double-Entry Accounting
Every transaction in Hearth is a transfer *between* two accounts. There is no money magically created or destroyed. Instead, money is routed via specific entries.
Every transaction has at least two **splits**, one debited, and the competing split identically credited.

### 1. Assets
Things you **own** that hold value.
- **Cash Accounts**: Checking, Savings, physical wallet.
- **Investments**: Stock portfolios, retirement funds, real estate.

### 2. Liabilities
Things you **owe** to external entities.
- **Credit Cards**: Balances owed to card issuers.
- **Loans**: Mortgages, student loans, auto loans.

### 3. Income
Money flowing **into** your possession from an external entity. You cannot own an income account; it strictly exists as a source.
- **Salary**: Paychecks from an employer.
- **Interest**: Yields from savings or capital gains.

### 4. Expenses
Money flowing **out of** your possession to an external entity.
- **Groceries**: Purchases for food.
- **Utilities**: Bills like electricity, internet, heating.

### 5. Equity (Net Worth)
Your overall worth. It is fundamentally calculated as:

```
Equity = Assets - Liabilities
```

If you own $10,000 (Asset) and owe $2,000 (Liability), your clear baseline equity is $8,000. Operating statements build off this core formula.

### Splits
Because this system leverages Double-Entry structures, every `Transaction` object has numerous `Splits` mapping the value distributions clearly. If you are ever confused where money exists, examine the raw splits within any single transaction ID.
