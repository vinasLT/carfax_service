from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from api.carfax_api import CarfaxAPIClient
from config import settings
from core.logger import logger
from database.crud.base import BaseService
from database.models.carfax_purchases import CarfaxPurchase
from database.schemas.carfax_purchases import CarfaxPurchaseCreate, CarfaxPurchaseUpdate, CarfaxPurchaseRead
from rpc_client_server.checkout_stripe_client import get_checkout_link


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

    async def get_vin_for_user_or_create(
        self,
        external_user_id: str,
        source: str,
        vin: str,
        auction: str | None = None,
        lot_id: str | None = None,
    ) -> CarfaxPurchase:
        carfax = await self.get_vin_for_user(external_user_id, source, vin)
        if not carfax:
            carfax = await self.create(CarfaxPurchaseCreate(
                user_external_id=external_user_id,
                source=source,
                vin=vin.upper(),
                auction=auction,
                lot_id=lot_id,
            ))
            return carfax

        update_data = {}
        if auction is not None and not carfax.auction:
            update_data["auction"] = auction
        if lot_id is not None and not carfax.lot_id:
            update_data["lot_id"] = lot_id
        if update_data:
            carfax = await self.update(carfax.id, CarfaxPurchaseUpdate(**update_data))
        return carfax

    async def create_purchase_with_checkout(
            self,
            user_external_id: str,
            source: str,
            vin: str,
            auction: str | None = None,
            lot_id: str | None = None,
            success_link: str = settings.SUCCESS_PAYMENT_URL,
            cancel_link: str = settings.COMPANY_LINK,
    ) -> tuple[CarfaxPurchase, str]:
        carfax = await self.get_vin_for_user_or_create(
            external_user_id=user_external_id,
            source=source,
            vin=vin,
            auction=auction,
            lot_id=lot_id,
        )
        link = await get_checkout_link(
            purpose_external_id=str(carfax.id),
            success_link=success_link,
            cancel_link=cancel_link,
            user_external_id=user_external_id,
            source=source
        )

        return carfax, link

    async def get_carfax_with_link(self, user_external_id: str,
            source: str,
            vin: str):
        carfax = await self.get_vin_for_user(user_external_id, source, vin)
        if not carfax:
            logger.warning(
                "Carfax not found for user",
                extra={
                    'vin': vin,
                    'user_external_id': user_external_id,
                    'source': source
                }
            )
            return None
        api = CarfaxAPIClient()
        if carfax.is_paid and not carfax.link:
            already_in_db = await self.get_by_vin(vin=carfax.vin)
            if already_in_db and already_in_db.link:
                carfax = await self.update(carfax.id, CarfaxPurchaseUpdate(link=already_in_db.link))
            else:
                carfax_api = await api.get_carfax(carfax.vin)
                carfax = await self.update(
                    carfax.id, CarfaxPurchaseUpdate(link=str(carfax_api.file))
                )
                logger.info(
                    "Successfully retrieved carfax from API",
                    extra={'carfax_id': carfax.id, 'vin': vin}
                )
        return carfax







    async def get_by_vin(self, vin: str) -> CarfaxPurchase:
        query = select(CarfaxPurchase).where(
            CarfaxPurchase.vin == vin.upper(),
            CarfaxPurchase.link.is_not(None),
            CarfaxPurchase.is_paid.is_(True),
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    def get_all_for_user_stmt(self, external_user_id: str, source: str):
        return select(CarfaxPurchase).where(
            CarfaxPurchase.user_external_id == external_user_id,
            CarfaxPurchase.source == source,
        ).order_by(desc(CarfaxPurchase.created_at))

    async def get_all_for_user(self, external_user_id: str, source: str) -> list[CarfaxPurchaseRead]:
        result = await self.session.execute(self.get_all_for_user_stmt(external_user_id, source))
        purchases = result.scalars().all()
        return [CarfaxPurchaseRead.model_validate(p) for p in purchases]
