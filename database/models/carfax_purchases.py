from datetime import datetime, UTC

from sqlalchemy import Column, Integer, String, DateTime, Index, Boolean
from sqlalchemy.orm import relationship

from database.models import Base

class CarfaxPurchase(Base):
    __tablename__ = "carfax_purchase"

    id = Column(Integer, primary_key=True)
    user_external_id = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False, index=True)
    link = Column(String, nullable=True)
    is_paid = Column(Boolean, nullable=False, default=False)
    vin = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index('ix_user_source', 'user_external_id', 'source'),
    )
