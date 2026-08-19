from app.core.security import hash_password
from app.models.enums import RoleEnum
from app.models.user import User
from tests.api.test_orders import _funded_investor, _instrument, _login


def _role_token(client, db, email, role):
    user = User(email=email, password_hash=hash_password("StrongPass123!"), full_name="Staff", role=role)
    db.add(user)
    db.commit()
    return _login(client, email)


def test_list_and_get_users(client, db):
    _funded_investor(db, "adminview1@x.com")
    token = _role_token(client, db, "admin1@x.com", RoleEnum.admin)
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/v1/backoffice/users", headers=headers)
    assert r.status_code == 200
    assert any(u["email"] == "adminview1@x.com" for u in r.json())

    user_id = next(u["id"] for u in r.json() if u["email"] == "adminview1@x.com")
    r = client.get(f"/api/v1/backoffice/users/{user_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "adminview1@x.com"


def test_only_super_admin_can_change_role(client, db):
    _funded_investor(db, "roletarget@x.com")
    admin_token = _role_token(client, db, "admin2@x.com", RoleEnum.admin)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    users = client.get("/api/v1/backoffice/users", headers=admin_headers).json()
    target_id = next(u["id"] for u in users if u["email"] == "roletarget@x.com")

    r = client.patch(f"/api/v1/backoffice/users/{target_id}/role", headers=admin_headers, json={"role": "admin"})
    assert r.status_code == 403  # plain admin can't grant roles

    super_token = _role_token(client, db, "superadmin1@x.com", RoleEnum.super_admin)
    super_headers = {"Authorization": f"Bearer {super_token}"}
    r = client.patch(f"/api/v1/backoffice/users/{target_id}/role", headers=super_headers, json={"role": "admin"})
    assert r.status_code == 200
    assert r.json()["role"] == "admin"

    # audit trail recorded
    r = client.get("/api/v1/backoffice/audit-log", headers=super_headers, params={"action": "user.role_change"})
    assert r.status_code == 200
    assert any(e["entity_id"] == target_id for e in r.json())


def test_suspend_account_blocks_new_orders(client, db):
    user, account = _funded_investor(db, "suspendme@x.com")
    instrument = _instrument(db, "SUSP1", "10.00")
    backoffice_token = _role_token(client, db, "backoffice1@x.com", RoleEnum.backoffice_operator)
    bo_headers = {"Authorization": f"Bearer {backoffice_token}"}

    r = client.patch(
        f"/api/v1/backoffice/accounts/{account.id}/status", headers=bo_headers, json={"status": "suspended"}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "suspended"

    investor_token = _login(client, "suspendme@x.com")
    investor_headers = {"Authorization": f"Bearer {investor_token}"}
    r = client.post(
        "/api/v1/orders", headers=investor_headers,
        json={"instrument_id": str(instrument.id), "side": "buy", "order_type": "market", "quantity": "1"},
    )
    assert r.status_code == 201
    assert r.json()["status"] == "rejected"
    assert "not active" in r.json()["rejection_reason"]


def test_backoffice_sees_all_orders_and_executions(client, db):
    user, account = _funded_investor(db, "boorders1@x.com")
    instrument = _instrument(db, "BOORD1", "25.00")
    investor_token = _login(client, "boorders1@x.com")
    r = client.post(
        "/api/v1/orders", headers={"Authorization": f"Bearer {investor_token}"},
        json={"instrument_id": str(instrument.id), "side": "buy", "order_type": "market", "quantity": "2"},
    )
    order_id = r.json()["id"]

    bo_token = _role_token(client, db, "boorders_staff@x.com", RoleEnum.backoffice_operator)
    bo_headers = {"Authorization": f"Bearer {bo_token}"}

    r = client.get("/api/v1/backoffice/orders", headers=bo_headers)
    assert r.status_code == 200
    assert any(o["id"] == order_id for o in r.json())

    r = client.get("/api/v1/backoffice/executions", headers=bo_headers)
    assert r.status_code == 200
    assert any(e["order_id"] == order_id for e in r.json())

    r = client.get("/api/v1/backoffice/ledger", headers=bo_headers, params={"account_id": str(account.id)})
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_settings_read_and_super_admin_only_write(client, db):
    bo_token = _role_token(client, db, "bosettings@x.com", RoleEnum.backoffice_operator)
    bo_headers = {"Authorization": f"Bearer {bo_token}"}

    r = client.get("/api/v1/backoffice/settings", headers=bo_headers)
    assert r.status_code == 200

    r = client.patch(
        "/api/v1/backoffice/settings/fee_rate_bps", headers=bo_headers, json={"value": {"bps": 20}}
    )
    assert r.status_code == 403

    super_token = _role_token(client, db, "supersettings@x.com", RoleEnum.super_admin)
    super_headers = {"Authorization": f"Bearer {super_token}"}
    r = client.patch(
        "/api/v1/backoffice/settings/fee_rate_bps", headers=super_headers, json={"value": {"bps": 20}}
    )
    assert r.status_code == 200
    assert r.json()["value"] == {"bps": 20}


def test_investor_forbidden_from_all_backoffice_admin_routes(client, db):
    _funded_investor(db, "plaininvestor@x.com")
    token = _login(client, "plaininvestor@x.com")
    headers = {"Authorization": f"Bearer {token}"}

    for path in ["/api/v1/backoffice/users", "/api/v1/backoffice/accounts", "/api/v1/backoffice/orders",
                 "/api/v1/backoffice/executions", "/api/v1/backoffice/audit-log", "/api/v1/backoffice/settings"]:
        r = client.get(path, headers=headers)
        assert r.status_code == 403, path
