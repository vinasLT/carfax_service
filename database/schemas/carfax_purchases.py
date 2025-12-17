from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CarfaxPurchaseBase(BaseModel):
    user_external_id: str
    source: str
    link: Optional[str] = None
    is_paid: Optional[bool] = False
    vin: Optional[str] = None
    auction: Optional[str] = None
    lot_id: Optional[str] = None
    created_at: Optional[datetime] = None



class CarfaxPurchaseCreate(CarfaxPurchaseBase):
    pass


class CarfaxPurchaseUpdate(BaseModel):
    source: Optional[str] = None
    link: Optional[str] = None
    is_paid: Optional[bool] = False
    vin: Optional[str] = None
    auction: Optional[str] = None
    lot_id: Optional[str] = None


class CarfaxPurchaseRead(CarfaxPurchaseBase):
    id: int

    class Config:
        from_attributes = True

class CarfaxPurchaseReadWithoutId(CarfaxPurchaseBase):
    class Config:
        from_attributes = True
