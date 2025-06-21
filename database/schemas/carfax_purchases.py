from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl


class CarfaxPurchaseBase(BaseModel):
    user_external_id: str
    source: str
    link: HttpUrl
    vin: str
    created_at: Optional[datetime] = None


class CarfaxPurchaseCreate(CarfaxPurchaseBase):
    pass


class CarfaxPurchaseUpdate(BaseModel):
    source: Optional[str] = None
    link: Optional[HttpUrl] = None
    vin: Optional[str] = None


class CarfaxPurchaseRead(CarfaxPurchaseBase):
    id: int

    class Config:
        from_attributes = True