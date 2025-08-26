from pydantic import BaseModel, Field


class CarfaxPurchaseIn(BaseModel):
    source: str = Field('web', description='Source, for example: web, bot etc, default: web')
    vin: str = Field(..., description='VIN of vehicle')
