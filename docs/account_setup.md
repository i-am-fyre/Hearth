# Account Setup

Once Hearth is running, the next step is establishing your primary admin user.

## Primary Administrator
In the default database state, there is no root or admin user. Hearth requires the first created user to act as the primary owner for safety and management.

### Creating the Setup
1. Open the [SvelteKit Dashboard](http://localhost:5173).
2. The UI will detect a fresh installation and direct you to the **Setup Screen**.
3. Create your new user account safely:
   - Provide an exact email.
   - Enter a secure password.
4. Once completed, your session is authenticated, and the first user will implicitly have `admin` privileges assigned.

> [!CAUTION]
> It is extremely important that you remember the admin credentials. Without them, you will have to truncate your database to initiate a fresh setup again!

## Role Based Permissions

Users added subsequently by the original user will default to `Viewer` access unless altered in the UI settings pane.

* Proceed to [Accounting Terms](accounting_terms.md) to understand double-entry accounting.
