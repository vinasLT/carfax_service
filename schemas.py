from pydantic import BaseModel

class CarfaxPurchaseIn(BaseModel):
    user_external_id: str
    source: str
    vin: str
