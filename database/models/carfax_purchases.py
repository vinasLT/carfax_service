from datetime import datetime, UTC

from sqlalchemy import Boolean, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.models import Base


class CarfaxPurchase(Base):
    __tablename__ = "carfax_purchase"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_external_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String, nullable=False, index=True)
    link: Mapped[str | None] = mapped_column(String, nullable=True)
    is_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    vin: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    auction: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    lot_id: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        Index('ix_user_source', 'user_external_id', 'source'),
    )
