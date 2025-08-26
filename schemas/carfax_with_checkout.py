from pydantic import BaseModel

from database.schemas.carfax_purchases import CarfaxPurchaseRead


class CarfaxWithCheckoutOut(BaseModel):
    carfax: CarfaxPurchaseRead
    checkout_link: str
