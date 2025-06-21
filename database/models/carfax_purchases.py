from datetime import datetime, UTC

from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.orm import relationship

from database.models import Base

class CarfaxPurchase(Base):
    __tablename__ = "carfax_purchase"

    id = Column(Integer, primary_key=True)
    user_external_id = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False, index=True)
    link = Column(String, nullable=False, index=True)
    vin = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index('ix_user_source', 'user_external_id', 'source'),
    )

    links = relationship("CarfaxLink", back_populates="purchase")
