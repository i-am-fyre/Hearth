from tests.conftest import register


def make_account(client, headers, name, type_):
    r = client.post("/api/v1/accounts/", json={"name": name, "type": type_}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def balances(client, headers):
    r = client.get("/api/v1/accounts/", headers=headers)
    assert r.status_code == 200
    return {a["name"]: float(a["balance"]) for a in r.json()}


def entry(account_id, debit="0.00", credit="0.00"):
    return {"account_id": account_id, "debit": debit, "credit": credit}


def test_balanced_transaction_updates_balances(client):
    h = register(client, "alex@example.com")
    checking = make_account(client, h, "Checking", "asset")
    groceries = make_account(client, h, "Groceries", "expense")
    salary = make_account(client, h, "Salary", "income")

    for body in (
        {"date": "2026-11-01", "description": "Paycheque", "entries": [entry(checking, debit="2000.00"), entry(salary, credit="2000.00")]},
        {"date": "2026-11-02", "description": "Groceries", "entries": [entry(groceries, debit="123.45"), entry(checking, credit="123.45")]},
    ):
        r = client.post("/api/v1/transactions/", json=body, headers=h)
        assert r.status_code == 200, r.text

    assert balances(client, h) == {"Checking": 1876.55, "Groceries": 123.45, "Salary": 2000.00}
    assert len(client.get("/api/v1/transactions/", headers=h).json()) == 2


def test_unbalanced_transaction_is_rejected(client):
    h = register(client, "alex@example.com")
    checking = make_account(client, h, "Checking", "asset")
    groceries = make_account(client, h, "Groceries", "expense")

    r = client.post(
        "/api/v1/transactions/",
        json={"date": "2026-11-02", "description": "Oops", "entries": [entry(groceries, debit="10.00"), entry(checking, credit="9.99")]},
        headers=h,
    )
    assert r.status_code == 400
    assert balances(client, h) == {"Checking": 0.0, "Groceries": 0.0}


def test_users_cannot_see_or_post_to_each_others_accounts(client):
    alex = register(client, "alex@example.com")
    sam = register(client, "sam@example.com")
    alex_checking = make_account(client, alex, "Alex Checking", "asset")
    sam_expense = make_account(client, sam, "Sam Expense", "expense")

    assert balances(client, sam) == {"Sam Expense": 0.0}
    assert client.get(f"/api/v1/accounts/{alex_checking}", headers=sam).status_code == 404

    r = client.post(
        "/api/v1/transactions/",
        json={"date": "2026-11-02", "description": "Steal", "entries": [entry(sam_expense, debit="5.00"), entry(alex_checking, credit="5.00")]},
        headers=sam,
    )
    assert r.status_code == 400
