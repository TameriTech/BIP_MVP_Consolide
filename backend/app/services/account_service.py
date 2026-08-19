from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.account import Account
from app.models.user import User


def get_account_for_user(db: Session, user: User) -> Account:
    account = db.query(Account).filter(Account.user_id == user.id).first()
    if account is None:
        raise NotFoundError("account not found for this user")
    return account
