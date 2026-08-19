from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import RoleEnum
from app.models.mixins import TimestampMixin, UUIDPKMixin


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    role: Mapped[RoleEnum] = mapped_column(
        Enum(RoleEnum, name="role_enum"), nullable=False, default=RoleEnum.investor
    )

    account: Mapped["Account"] = relationship(back_populates="user", uselist=False)
