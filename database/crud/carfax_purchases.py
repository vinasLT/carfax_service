from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.base import BaseService
from database.models.carfax_purchases import CarfaxPurchase
from database.schemas.carfax_purchases import CarfaxPurchaseCreate, CarfaxPurchaseUpdate, CarfaxPurchaseRead


class CarfaxPurchasesService(BaseService[CarfaxPurchase, CarfaxPurchaseCreate, CarfaxPurchaseUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(CarfaxPurchase, session)

    async def get_vin_for_user(self, external_user_id: str, source: str, vin: str)-> CarfaxPurchase:
        query = select(CarfaxPurchase).where(
            CarfaxPurchase.vin == vin.upper(),
            CarfaxPurchase.user_external_id == external_user_id,
            CarfaxPurchase.source == source,
        )
        result = await self.session.execute(query)
        return result.scalars().first()


    async def get_by_vin(self, vin: str) -> CarfaxPurchase:
        query = select(CarfaxPurchase).where(
            CarfaxPurchase.vin == vin.upper(),
            CarfaxPurchase.link.is_not(None),
            CarfaxPurchase.is_paid.is_(True),
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_all_for_user(self, external_user_id: str, source: str) -> list[CarfaxPurchaseRead]:
        query = select(CarfaxPurchase).where(
            CarfaxPurchase.user_external_id == external_user_id,
            CarfaxPurchase.source == source,
        ).order_by(desc(CarfaxPurchase.created_at))
        result = await self.session.execute(query)
        purchases = result.scalars().all()
        return [CarfaxPurchaseRead.model_validate(p) for p in purchases]

