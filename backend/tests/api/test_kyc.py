from app.core.security import hash_password
from app.models.enums import RoleEnum
from app.models.user import User


def _register(client, email="investor@x.com"):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123!", "full_name": "Investor X"},
    )
    return r.json()


def _make_backoffice_user(db, email="reviewer@x.com"):
    user = User(
        email=email, password_hash=hash_password("StrongPass123!"), full_name="Reviewer",
        role=RoleEnum.backoffice_operator,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(client, email, password="StrongPass123!"):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


def test_kyc_draft_submit_validate_activates_account_and_credits_ledger(client, db):
    investor_tokens = _register(client, "investor1@x.com")
    investor_access = investor_tokens["access_token"]
    investor_headers = {"Authorization": f"Bearer {investor_access}"}

    r = client.get("/api/v1/kyc/me", headers=investor_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "draft"

    r = client.post(
        "/api/v1/kyc/me",
        headers=investor_headers,
        json={
            "full_legal_name": "Investor X",
            "birth_date": "1990-01-01",
            "country": "CI",
            "id_document_type": "passport",
            "id_document_number": "P123456",
        },
    )
    assert r.status_code == 200
    assert r.json()["full_legal_name"] == "Investor X"

    r = client.post("/api/v1/kyc/me/submit", headers=investor_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "submitted"
    kyc_id = r.json()["id"]

    reviewer = _make_backoffice_user(db, "reviewer1@x.com")
    reviewer_access = _login(client, "reviewer1@x.com")
    reviewer_headers = {"Authorization": f"Bearer {reviewer_access}"}

    r = client.get("/api/v1/backoffice/kyc?status_filter=submitted", headers=reviewer_headers)
    assert r.status_code == 200
    assert any(k["id"] == kyc_id for k in r.json())

    r = client.post(f"/api/v1/backoffice/kyc/{kyc_id}/validate", headers=reviewer_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "validated"

    from app.models.account import Account
    from app.models.enums import AccountStatus
    from app.models.ledger import LedgerEntry
    from app.models.user import User as UserModel

    user = db.query(UserModel).filter(UserModel.email == "investor1@x.com").first()
    account = db.query(Account).filter(Account.user_id == user.id).first()
    assert account.status == AccountStatus.active
    assert account.activated_at is not None
    assert account.cash_balance > 0
    assert account.cash_reserved == 0

    entries = db.query(LedgerEntry).filter(LedgerEntry.account_id == account.id).all()
    assert len(entries) == 1
    assert entries[0].entry_type.value == "initial_credit"
    assert entries[0].amount == account.cash_balance
    assert entries[0].balance_after == account.cash_balance


def test_investor_cannot_access_backoffice_kyc(client):
    tokens = _register(client, "investor2@x.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    r = client.get("/api/v1/backoffice/kyc", headers=headers)
    assert r.status_code == 403


def test_submit_incomplete_kyc_is_rejected(client):
    tokens = _register(client, "investor3@x.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    r = client.post("/api/v1/kyc/me/submit", headers=headers)
    assert r.status_code == 422


def test_reject_kyc_then_resubmit(client, db):
    tokens = _register(client, "investor4@x.com")
    investor_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    client.post(
        "/api/v1/kyc/me",
        headers=investor_headers,
        json={
            "full_legal_name": "Investor Four",
            "id_document_type": "passport",
            "id_document_number": "P999",
        },
    )
    r = client.post("/api/v1/kyc/me/submit", headers=investor_headers)
    kyc_id = r.json()["id"]

    _make_backoffice_user(db, "reviewer4@x.com")
    reviewer_access = _login(client, "reviewer4@x.com")
    reviewer_headers = {"Authorization": f"Bearer {reviewer_access}"}

    r = client.post(
        f"/api/v1/backoffice/kyc/{kyc_id}/reject", headers=reviewer_headers, json={"reason": "blurry document"}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"
    assert r.json()["rejection_reason"] == "blurry document"

    r = client.post(
        "/api/v1/kyc/me", headers=investor_headers, json={"id_document_number": "P999-NEW"}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "draft"
    assert r.json()["rejection_reason"] is None
