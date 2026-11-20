# Households

Hearth supports a multi-user **Household** system, allowing multiple individuals to manage shared finances or view each other's data while maintaining distinct user profiles.

## Core Concepts

A **Household** is a group of users who share access to a subset of financial data or live under a single "financial roof." Everyone in a household can see and edit each other's accounts and transactions, which is why nobody joins a household without accepting an invitation.

### Household Roles

There are three roles within a household:

| Role | Permissions |
|------|-------------|
| `owner` | Everything a member can do, plus inviting people, changing roles, removing members, and cancelling invitations. |
| `member` | Can view and change the household's accounts, transactions and budgets. Can leave the household. |
| `read_only` | Can view the household's accounts, transactions and budgets, but can only change their own. |

Read-only members see a **View only** label instead of edit and delete buttons on other
members' accounts, transactions and budgets, and can only post transactions (or reconcile
bank imports) between their own accounts. They can still create budgets and suggestion-only
rules that refer to shared accounts, since those only read them.

## Managing Your Household

Household settings live in **Settings** (the gear icon in the header), available on every page.

### Creating a Household
The first time you open Settings, Hearth automatically creates a household with you as its **Owner**.

### Inviting Members
Owners can invite people by email address. Every invitation starts as **pending** (shown as
*Invited*), whether or not the person already has a Hearth account. If email is configured,
they also receive an email telling them how to accept.

Inviting someone who is already a member changes their role instead.

### Accepting an Invitation
When someone invites you, an amber dot appears on the gear icon. Open **Settings** to see
*Invitations for you*, then **Accept** to join (or **Decline**). Invitations sent to an email
address before it was registered wait in the same place after you sign up.

### Removing Members and Leaving
- Owners can remove members, and cancel pending invitations, from Settings.
- Any member can **Leave household** from Settings.
- A household always keeps at least one owner. To leave as the last owner, first invite
  another member with the **Owner** role (re-inviting an existing member changes their role).

> [!NOTE]
> Leaving or being removed stops the sharing in both directions: you no longer see the
> household's accounts, and they no longer see yours. Your own data stays in your account.

## Privacy & Security

While households allow sharing, encryption keys for sensitive data (like receipt images) are managed per-user to ensure that private documents remain secure unless explicitly shared.
