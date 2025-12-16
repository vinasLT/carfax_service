from pydantic import BaseModel, Field


class CarfaxPurchaseIn(BaseModel):
    vin: str = Field(..., description='VIN of vehicle')
