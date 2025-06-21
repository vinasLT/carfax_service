from pydantic import BaseModel


class BuyCarfaxIn(BaseModel):
    vin: str
    user_id: str
    source: str


class CarfaxPurchaseIn(BaseModel):
    user_external_id: str
    source: str
    vin: str