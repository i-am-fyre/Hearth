"""Household membership: who can see whose data, and who may change membership."""
from tests.conftest import register


def make_account(client, headers, name):
    r = client.post("/api/v1/accounts/", json={"name": name, "type": "asset"}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def account_names(client, headers):
    return {a["name"] for a in client.get("/api/v1/accounts/", headers=headers).json()}


def household(client, headers):
    r = client.get("/api/v1/households/", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def invite(client, headers, email, role="member"):
    return client.post("/api/v1/households/invite", json={"email": email, "role": role}, headers=headers)


def my_invitations(client, headers):
    r = client.get("/api/v1/households/invitations", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def accept_only_invitation(client, headers):
    (inv,) = my_invitations(client, headers)
    r = client.post(f"/api/v1/households/invitations/{inv['id']}/accept", headers=headers)
    assert r.status_code == 200, r.text


def user_id(client, headers):
    return client.get("/api/v1/auth/me", headers=headers).json()["id"]


def remove(client, headers, uid):
    return client.delete(f"/api/v1/households/member/{uid}", headers=headers)


def test_inviting_an_existing_user_does_not_expose_their_data(client):
    """Inviting someone must not let you see their finances until they accept."""
    alex = register(client, "alex@example.com")
    sam = register(client, "sam@example.com")
    make_account(client, sam, "Sam Private Savings")

    r = invite(client, alex, "sam@example.com")
    assert r.status_code == 200
    assert r.json()["status"] == "invite_sent"

    assert "Sam Private Savings" not in account_names(client, alex)
    assert account_names(client, sam) == {"Sam Private Savings"}


def test_accepting_an_invitation_shares_the_household(client):
    alex = register(client, "alex@example.com")
    sam = register(client, "sam@example.com")
    make_account(client, alex, "Joint Chequing")
    invite(client, alex, "sam@example.com")

    (inv,) = my_invitations(client, sam)
    assert inv["household_name"] == household(client, alex)["name"]
    assert inv["owner_email"] == "alex@example.com"
    assert inv["role"] == "member"
    accept_only_invitation(client, sam)

    assert "Joint Chequing" in account_names(client, sam)
    emails = {m["email"]: m["status"] for m in household(client, alex)["members"]}
    assert emails == {"alex@example.com": "active", "sam@example.com": "active"}
    assert my_invitations(client, sam) == []


def test_declining_an_invitation_shares_nothing(client):
    alex = register(client, "alex@example.com")
    sam = register(client, "sam@example.com")
    make_account(client, alex, "Alex Only")
    invite(client, alex, "sam@example.com")

    (inv,) = my_invitations(client, sam)
    assert client.delete(f"/api/v1/households/invitations/{inv['id']}", headers=sam).status_code == 200

    assert my_invitations(client, sam) == []
    assert "Alex Only" not in account_names(client, sam)
    assert [m["email"] for m in household(client, alex)["members"]] == ["alex@example.com"]


def test_signing_up_does_not_auto_join_an_inviting_household(client):
    alex = register(client, "alex@example.com")
    make_account(client, alex, "Alex Only")
    invite(client, alex, "newcomer@example.com")

    newcomer = register(client, "newcomer@example.com")
    assert account_names(client, newcomer) == set()
    assert len(my_invitations(client, newcomer)) == 1

    accept_only_invitation(client, newcomer)
    assert "Alex Only" in account_names(client, newcomer)


def test_only_owners_invite_or_remove_others(client):
    alex = register(client, "alex@example.com")
    sam = register(client, "sam@example.com")
    register(client, "chris@example.com")
    invite(client, alex, "sam@example.com")
    accept_only_invitation(client, sam)

    assert invite(client, sam, "chris@example.com").status_code == 403
    assert remove(client, sam, user_id(client, alex)).status_code == 403
    # Re-inviting an existing member is how roles change; members can't promote themselves.
    assert invite(client, sam, "sam@example.com", role="owner").status_code == 403
    roles = {m["email"]: m["role"] for m in household(client, alex)["members"]}
    assert roles == {"alex@example.com": "owner", "sam@example.com": "member"}


def test_members_can_leave_and_owners_can_remove(client):
    alex = register(client, "alex@example.com")
    sam = register(client, "sam@example.com")
    chris = register(client, "chris@example.com")
    make_account(client, alex, "Joint Chequing")
    for email, headers in (("sam@example.com", sam), ("chris@example.com", chris)):
        invite(client, alex, email)
        accept_only_invitation(client, headers)

    assert remove(client, sam, user_id(client, sam)).status_code == 200  # Sam leaves
    assert "Joint Chequing" not in account_names(client, sam)

    assert remove(client, alex, user_id(client, chris)).status_code == 200  # owner removes Chris
    assert "Joint Chequing" not in account_names(client, chris)


def test_last_owner_cannot_leave_or_be_removed(client):
    alex = register(client, "alex@example.com")
    sam = register(client, "sam@example.com")
    invite(client, alex, "sam@example.com", role="owner")
    accept_only_invitation(client, sam)

    # With two owners, one may leave...
    assert remove(client, sam, user_id(client, sam)).status_code == 200
    # ...but the last one can't.
    r = remove(client, alex, user_id(client, alex))
    assert r.status_code == 400
    assert "at least one owner" in r.json()["detail"]


def test_owner_can_cancel_a_pending_invitation_but_strangers_cannot(client):
    alex = register(client, "alex@example.com")
    chris = register(client, "chris@example.com")
    invite(client, alex, "pending@example.com")
    pending = next(m for m in household(client, alex)["members"] if m["status"] == "pending")

    # Someone outside the household can't cancel it, accept it, or tell that it exists.
    assert client.delete(f"/api/v1/households/invitations/{pending['id']}", headers=chris).status_code == 404
    assert client.post(f"/api/v1/households/invitations/{pending['id']}/accept", headers=chris).status_code == 404

    assert client.delete(f"/api/v1/households/invitations/{pending['id']}", headers=alex).status_code == 200
    assert [m["email"] for m in household(client, alex)["members"]] == ["alex@example.com"]


def test_cannot_invite_yourself(client):
    alex = register(client, "alex@example.com")
    assert invite(client, alex, "alex@example.com").status_code == 400
