"""Household roles: read-only members can view shared data but change only their own.

Also covers write paths that used to accept any account ID in the database.
"""
import json

import pytest
from sqlalchemy import text

from tests.conftest import register

READ_ONLY = "You have read-only access to this household's data."


def account(client, h, name, type_="asset"):
    r = client.post("/api/v1/accounts/", json={"name": name, "type": type_}, headers=h)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def txn_body(debit_acc, credit_acc, amount="20.00", description="Groceries"):
    return {
        "date": "2026-11-02",
        "description": description,
        "entries": [
            {"account_id": debit_acc, "debit": amount, "credit": "0.00"},
            {"account_id": credit_acc, "debit": "0.00", "credit": amount},
        ],
    }


def join(client, owner_h, email, h, role):
    r = client.post("/api/v1/households/invite", json={"email": email, "role": role}, headers=owner_h)
    assert r.status_code == 200, r.text
    (inv,) = client.get("/api/v1/households/invitations", headers=h).json()
    assert client.post(f"/api/v1/households/invitations/{inv['id']}/accept", headers=h).status_code == 200


def by_id(items):
    return {i["id"]: i for i in items}


def upload_csv(client, h, rows, source_account_id=None):
    csv = "Date,Description,Amount\n" + "".join(f"{d},{desc},{amt}\n" for d, desc, amt in rows)
    config = {"has_header": True, "date_col": 0, "desc_col": 1, "amount_col": 2,
              "source_account_id": source_account_id}
    r = client.post(
        "/api/v1/imports/csv",
        files={"file": ("bank.csv", csv.encode(), "text/csv")},
        data={"config": json.dumps(config)},
        headers=h,
    )
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture
def hh(client):
    """Alex owns a household with a read-only viewer and a regular member; a stranger is outside it."""
    alex = register(client, "alex@example.com")
    viewer = register(client, "viewer@example.com")
    member = register(client, "member@example.com")
    stranger = register(client, "stranger@example.com")

    chequing = account(client, alex, "Joint Chequing")
    groceries = account(client, alex, "Groceries", "expense")
    r = client.post("/api/v1/transactions/", json=txn_body(groceries, chequing), headers=alex)
    assert r.status_code == 200, r.text
    txn = r.json()["id"]
    r = client.post("/api/v1/budgets/", json={"name": "November", "month": 11, "year": 2026}, headers=alex)
    budget = r.json()["id"]

    join(client, alex, "viewer@example.com", viewer, "read_only")
    join(client, alex, "member@example.com", member, "member")

    return dict(client=client, alex=alex, viewer=viewer, member=member, stranger=stranger,
                chequing=chequing, groceries=groceries, txn=txn, budget=budget)


def balances(client, h):
    return {a["name"]: float(a["balance"]) for a in client.get("/api/v1/accounts/", headers=h).json()}


# --- read-only members -------------------------------------------------------------

def test_viewer_sees_household_data_marked_read_only(hh):
    c, v = hh["client"], hh["viewer"]
    own = account(c, v, "Viewer Wallet")

    accounts = by_id(c.get("/api/v1/accounts/", headers=v).json())
    assert accounts[hh["chequing"]]["can_edit"] is False
    assert accounts[own]["can_edit"] is True
    assert by_id(c.get("/api/v1/transactions/", headers=v).json())[hh["txn"]]["can_edit"] is False
    assert by_id(c.get("/api/v1/budgets/", headers=v).json())[hh["budget"]]["can_edit"] is False


def test_viewer_cannot_change_shared_accounts(hh):
    c, v = hh["client"], hh["viewer"]
    r = c.put(f"/api/v1/accounts/{hh['chequing']}", json={"name": "Hacked"}, headers=v)
    assert (r.status_code, r.json()["detail"]) == (403, READ_ONLY)
    assert c.delete(f"/api/v1/accounts/{hh['chequing']}", headers=v).status_code == 403
    assert "Joint Chequing" in balances(c, hh["alex"])


def test_viewer_cannot_post_or_edit_shared_transactions(hh):
    c, v = hh["client"], hh["viewer"]
    own = account(c, v, "Viewer Wallet")
    before = balances(c, hh["alex"])

    assert c.post("/api/v1/transactions/", json=txn_body(hh["groceries"], hh["chequing"]), headers=v).status_code == 403
    # Mixing one of their own accounts with a shared one is still a write to the shared one.
    assert c.post("/api/v1/transactions/", json=txn_body(hh["groceries"], own), headers=v).status_code == 403
    assert c.patch(f"/api/v1/transactions/{hh['txn']}", json={"description": "x"}, headers=v).status_code == 403
    assert c.delete(f"/api/v1/transactions/{hh['txn']}", headers=v).status_code == 403

    assert balances(c, hh["alex"]) == before


def test_viewer_cannot_change_shared_budgets(hh):
    c, v = hh["client"], hh["viewer"]
    line = {"account_id": hh["groceries"], "planned_amount": "100.00"}
    assert c.post(f"/api/v1/budgets/{hh['budget']}/lines", json=line, headers=v).status_code == 403
    assert c.delete(f"/api/v1/budgets/{hh['budget']}", headers=v).status_code == 403
    assert hh["budget"] in by_id(c.get("/api/v1/budgets/", headers=hh["alex"]).json())


def test_viewer_cannot_reconcile_imports_into_shared_accounts(hh):
    c, v = hh["client"], hh["viewer"]
    wallet = account(c, v, "Viewer Wallet")
    snacks = account(c, v, "Viewer Snacks", "expense")
    (bank_txn,) = upload_csv(c, v, [("2026-11-03", "Corner Store", "-4.50")])

    shared = {"bank_txn_id": bank_txn["id"], "source_account_id": hh["chequing"], "target_account_id": snacks}
    assert c.post("/api/v1/imports/reconcile", json=shared, headers=v).status_code == 403

    own = {"bank_txn_id": bank_txn["id"], "source_account_id": wallet, "target_account_id": snacks}
    assert c.post("/api/v1/imports/reconcile", json=own, headers=v).status_code == 200


def test_viewer_rules_may_suggest_but_not_auto_post_to_shared_accounts(hh):
    c, v = hh["client"], hh["viewer"]
    rule = {"condition_json": {"merchant_contains": "store"}, "action_json": {"assign_account_id": hh["groceries"]}}
    assert c.post("/api/v1/rules/", json={**rule, "auto_post": True}, headers=v).status_code == 403
    r = c.post("/api/v1/rules/", json={**rule, "auto_post": False}, headers=v)
    assert r.status_code == 200
    # ...and can't switch auto-post on afterwards.
    assert c.patch(f"/api/v1/rules/{r.json()['id']}", json={"auto_post": True}, headers=v).status_code == 403


def test_viewer_can_still_manage_their_own_data(hh):
    c, v = hh["client"], hh["viewer"]
    wallet = account(c, v, "Viewer Wallet")
    snacks = account(c, v, "Viewer Snacks", "expense")

    r = c.post("/api/v1/transactions/", json=txn_body(snacks, wallet, "5.00"), headers=v)
    assert r.status_code == 200
    txn = r.json()["id"]
    assert c.patch(f"/api/v1/transactions/{txn}", json={"description": "Chips"}, headers=v).status_code == 200
    assert c.put(f"/api/v1/accounts/{wallet}", json={"name": "Wallet"}, headers=v).status_code == 200

    budget = c.post("/api/v1/budgets/", json={"name": "Mine", "month": 11, "year": 2026}, headers=v).json()["id"]
    # Tracking a shared account in your own budget only reads it.
    for acc in (snacks, hh["groceries"]):
        line = {"account_id": acc, "planned_amount": "50.00"}
        assert c.post(f"/api/v1/budgets/{budget}/lines", json=line, headers=v).status_code == 200
    assert c.delete(f"/api/v1/transactions/{txn}", headers=v).status_code == 200
    assert c.delete(f"/api/v1/budgets/{budget}", headers=v).status_code == 200


# --- regular members and owners keep full access -------------------------------------

def test_members_can_change_shared_data(hh):
    c, m = hh["client"], hh["member"]
    assert by_id(c.get("/api/v1/accounts/", headers=m).json())[hh["chequing"]]["can_edit"] is True
    assert c.put(f"/api/v1/accounts/{hh['chequing']}", json={"name": "Chequing"}, headers=m).status_code == 200
    assert c.post("/api/v1/transactions/", json=txn_body(hh["groceries"], hh["chequing"]), headers=m).status_code == 200
    assert c.patch(f"/api/v1/transactions/{hh['txn']}", json={"description": "Weekly shop"}, headers=m).status_code == 200
    line = {"account_id": hh["groceries"], "planned_amount": "400.00"}
    assert c.post(f"/api/v1/budgets/{hh['budget']}/lines", json=line, headers=m).status_code == 200


def test_owner_can_change_a_read_only_members_data(hh):
    c = hh["client"]
    wallet = account(c, hh["viewer"], "Viewer Wallet")
    assert c.put(f"/api/v1/accounts/{wallet}", json={"name": "Renamed"}, headers=hh["alex"]).status_code == 200


# --- outsiders, and write paths that accepted any account ID -------------------------

def test_outsiders_get_not_found(hh):
    c, s = hh["client"], hh["stranger"]
    assert c.put(f"/api/v1/accounts/{hh['chequing']}", json={"name": "x"}, headers=s).status_code == 404
    assert c.patch(f"/api/v1/transactions/{hh['txn']}", json={"description": "x"}, headers=s).status_code == 404
    assert c.delete(f"/api/v1/budgets/{hh['budget']}", headers=s).status_code == 404
    own = account(c, s, "Stranger Cash")
    assert c.post("/api/v1/transactions/", json=txn_body(hh["groceries"], own), headers=s).status_code == 400


def test_editing_entries_cannot_target_other_peoples_accounts(hh):
    c, s = hh["client"], hh["stranger"]
    cash = account(c, s, "Stranger Cash")
    fun = account(c, s, "Stranger Fun", "expense")
    txn = c.post("/api/v1/transactions/", json=txn_body(fun, cash, "10.00"), headers=s).json()["id"]
    before = balances(c, hh["alex"])

    body = {"entries": txn_body(hh["groceries"], hh["chequing"], "999.00")["entries"]}
    assert c.patch(f"/api/v1/transactions/{txn}", json=body, headers=s).status_code == 400
    assert balances(c, hh["alex"]) == before


def test_reconcile_cannot_target_other_peoples_accounts(hh):
    c, s = hh["client"], hh["stranger"]
    cash = account(c, s, "Stranger Cash")
    (bank_txn,) = upload_csv(c, s, [("2026-11-03", "Transfer", "-50.00")])
    body = {"bank_txn_id": bank_txn["id"], "source_account_id": cash, "target_account_id": hh["groceries"]}
    assert c.post("/api/v1/imports/reconcile", json=body, headers=s).status_code == 400
    assert balances(c, hh["alex"])["Groceries"] == 20.0


def test_import_suggestions_never_reveal_other_peoples_accounts(hh, db_engine):
    c, s = hh["client"], hh["stranger"]
    # A rule can't be created pointing at someone else's account...
    rule = {"condition_json": {"merchant_contains": "grocer"}, "action_json": {"assign_account_id": hh["groceries"]}}
    assert c.post("/api/v1/rules/", json=rule, headers=s).status_code == 400
    # ...and one that already does (from before this check existed) reveals nothing.
    stranger_id = c.get("/api/v1/auth/me", headers=s).json()["id"]
    with db_engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO rules (user_id, priority, condition_json, action_json, active, auto_post) "
            "VALUES (:u, 1, CAST(:c AS JSON), CAST(:a AS JSON), true, false)"
        ), {"u": stranger_id, "c": json.dumps(rule["condition_json"]), "a": json.dumps(rule["action_json"])})

    (bank_txn,) = upload_csv(c, s, [("2026-11-03", "Big Grocer", "-30.00")])
    assert bank_txn["suggested_account_id"] is None
    assert bank_txn["suggested_account_name"] is None


def test_transactions_cannot_point_at_someone_elses_receipt(hh, db_engine):
    c = hh["client"]
    alex_id = c.get("/api/v1/auth/me", headers=hh["alex"]).json()["id"]
    with db_engine.begin() as conn:
        receipt_id = conn.execute(text(
            "INSERT INTO receipts (user_id, file_path, original_filename, mime_type, status, created_at) "
            "VALUES (:u, 'f', 'r.jpg', 'image/jpeg', 'pending', now()) RETURNING id"
        ), {"u": alex_id}).scalar_one()

    s = hh["stranger"]
    cash = account(c, s, "Stranger Cash")
    fun = account(c, s, "Stranger Fun", "expense")
    body = {**txn_body(fun, cash, "1.00"), "receipt_id": receipt_id}
    assert c.post("/api/v1/transactions/", json=body, headers=s).status_code == 404


def _receipt_for(client, h, db_engine):
    uid = client.get("/api/v1/auth/me", headers=h).json()["id"]
    with db_engine.begin() as conn:
        return conn.execute(text(
            "INSERT INTO receipts (user_id, file_path, original_filename, mime_type, status, created_at) "
            "VALUES (:u, 'f', 'r.jpg', 'image/jpeg', 'pending', now()) RETURNING id"
        ), {"u": uid}).scalar_one()


def test_attaching_receipts_follows_household_write_access(hh, db_engine):
    c, txn = hh["client"], hh["txn"]
    viewer_receipt = _receipt_for(c, hh["viewer"], db_engine)
    r = c.patch(f"/api/v1/receipts/{viewer_receipt}/attach", json={"transaction_id": txn}, headers=hh["viewer"])
    assert (r.status_code, r.json()["detail"]) == (403, READ_ONLY)

    member_receipt = _receipt_for(c, hh["member"], db_engine)
    r = c.patch(f"/api/v1/receipts/{member_receipt}/attach", json={"transaction_id": txn}, headers=hh["member"])
    assert r.status_code == 200, r.text

    stranger_receipt = _receipt_for(c, hh["stranger"], db_engine)
    r = c.patch(f"/api/v1/receipts/{stranger_receipt}/attach", json={"transaction_id": txn}, headers=hh["stranger"])
    assert r.status_code == 404


def test_reprocess_receipts_endpoint_works(hh):
    """This endpoint used to crash with a NameError (Receipt wasn't imported)."""
    r = hh["client"].post("/api/v1/receipts/reprocess", headers=hh["alex"])
    assert r.status_code == 200, r.text
