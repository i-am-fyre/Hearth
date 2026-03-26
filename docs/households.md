# Households

Hearth supports a multi-user **Household** system, allowing multiple individuals to manage shared finances or view each other's data while maintaining distinct user profiles.

## Core Concepts

A **Household** is a group of users who share access to a subset of financial data or live under a single "financial roof."

### Household Roles

There are three primary roles within a household:

| Role | Permissions |
|------|-------------|
| `owner` | Full management of the household, including renaming and inviting/removing members. |
| `member` | Standard access to household data and shared accounts. |
| `read_only` | Can view transactions and reports but cannot create or modify data. |

## Managing Your Household

### Creating a Household
By default, the first time you access the household settings, Hearth automatically initializes a household with you as the **Owner**.

### Inviting Members
You can invite members to your household via their email address.
- **Active Members**: If the user already has an Hearth account, they are added to the household immediately.
- **Pending Invitations**: If the email is not registered, an invitation is sent. These members appear with a **Pending** status until they create an account.

### Registration Auto-Join
Hearth simplifies onboarding for new users. When an invited person registers using the exact email address from the invitation, they are **automatically joined** to the household and granted the assigned role (Owner, Member, or Read-Only) upon their first login.

### Removing Members
Owners can remove users from the household at any time via the Household Settings pane.

> [!NOTE]
> Currently, Hearth accounts are logically tied to the household. Deleting a household member removes their association with the shared accounts, but their individual user history remains in the database.

## Privacy & Security

While households allow sharing, encryption keys for sensitive data (like receipt images) are managed per-user to ensure that private documents remain secure unless explicitly shared.
