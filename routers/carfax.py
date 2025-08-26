from fastapi import APIRouter, Body, Depends, Query, HTTPException
from rfc9457 import BadRequestProblem, NotFoundProblem, ServerProblem
from sqlalchemy.ext.asyncio import AsyncSession

from api.carfax_api import CarfaxAPIClient
from config import settings
from core.logger import logger
from database import get_db
from database.crud.carfax_purchases import CarfaxPurchasesService
from database.schemas.carfax_purchases import CarfaxPurchaseRead, CarfaxPurchaseCreate, CarfaxPurchaseUpdate
from dependencies.carfax_client import get_carfax_client
from dependencies.get_user import User, get_user
from rpc_client_server.checkout_stripe_client import StripeClient, get_checkout_link
from schemas.carfax_purchase import CarfaxPurchaseIn
from schemas.carfax_with_checkout import CarfaxWithCheckoutOut

carfax_router = APIRouter()


@carfax_router.post("/carfax/buy-carfax", response_model=CarfaxWithCheckoutOut, summary='Buy new carfax', description="Create buy carfax obj and get checkout link")
async def buy_carfax_request(
        user: User = Depends(get_user),
        data: CarfaxPurchaseIn = Body(...),
        db: AsyncSession = Depends(get_db),
        api: CarfaxAPIClient = Depends(get_carfax_client),
) -> CarfaxWithCheckoutOut:
    logger.info(
        "Starting carfax purchase request",
        extra={'vin': data.vin, 'user_external_id': user.id}
    )

    try:
        response = await api.check_balance()
        if response.balance <= 1:
            logger.error("Insufficient carfax balance", extra={'balance': response.balance})
            raise BadRequestProblem(detail='No carfaxes left, admin need to top up his account')

        is_exist = await api.check_if_vin_exists(vin=data.vin)
        if not is_exist:
            logger.warning("VIN not found", extra={'vin': data.vin})
            raise NotFoundProblem(detail='VIN not found')


        service = CarfaxPurchasesService(db)
        carfax, link = await service.create_purchase_with_checkout(
            user_external_id=user.id,
            source=data.source,
            vin=data.vin
        )

        logger.info(
            "Carfax purchase request completed",
            extra={'carfax_id': carfax.id, 'vin': data.vin}
        )

        carfax = CarfaxPurchaseRead.model_validate(carfax)
        return CarfaxWithCheckoutOut(carfax=carfax, checkout_link=link)

    except Exception as e:
        logger.error(
            "Error in carfax purchase",
            extra={'vin': data.vin, 'error': str(e)},
            exc_info=True
        )
        raise


@carfax_router.get("/carfax", response_model=list[CarfaxPurchaseRead], summary='Get all user carfaxes')
async def get_carfaxes(
        user: User = Depends(get_user),
        source: str = Query('web', description='Source, for example: web, bot etc, default: web'),
        db: AsyncSession = Depends(get_db)
):
    logger.info("Getting carfaxes for user", extra={'user_external_id': user.id})

    try:
        service = CarfaxPurchasesService(db)
        carfaxes = await service.get_all_for_user(user.id, source)

        logger.info("Retrieved carfaxes", extra={'count': len(carfaxes)})
        return carfaxes

    except Exception as e:
        logger.error(
            "Error getting carfaxes",
            extra={'user_external_id': user.id, 'error': str(e)},
            exc_info=True
        )
        raise


@carfax_router.get("/carfax/{vin}/", response_model=CarfaxPurchaseRead, description="Get carfax by VIN for user")
async def get_carfax_by_vin(
        vin: str,
        user: User = Depends(get_user),
        source: str = Query('web', description='Source, for example: web, bot etc, default: web'),
        db: AsyncSession = Depends(get_db),
) -> CarfaxPurchaseRead:
    logger.info(
        "Getting carfax by VIN",
        extra={
            'vin': vin,
            'user_external_id': user.id,
            'source': source,
            'endpoint': 'get_carfax_by_vin'
        }
    )

    try:
        service = CarfaxPurchasesService(db)
        carfax = await service.get_carfax_with_link(
            user_external_id=user.id,
            source=source,
            vin=vin
        )

        return CarfaxPurchaseRead.model_validate(carfax).model_dump()

    except Exception as e:
        logger.error(
            "Error getting carfax by VIN",
            extra={
                'vin': vin,
                'user_external_id': user.id,
                'source': source,
                'error': str(e),
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        raise ServerProblem(detail='Internal server error') from e