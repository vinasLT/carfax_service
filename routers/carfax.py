from AuthTools import HeaderUser
from fastapi import APIRouter, Body, Depends
from rfc9457 import BadRequestProblem, NotFoundProblem, ServerProblem
from sqlalchemy.ext.asyncio import AsyncSession
from AuthTools.Permissions.dependencies import require_permissions
from fastapi_pagination.ext.sqlalchemy import paginate

from api.carfax_api import CarfaxAPIClient
from config import Permissions
from core.logger import logger
from core.utils import create_pagination_page
from database import get_db
from database.crud.carfax_purchases import CarfaxPurchasesService
from database.schemas.carfax_purchases import CarfaxPurchaseRead
from dependencies.carfax_client import get_carfax_client
from schemas.carfax_purchase import CarfaxPurchaseIn
from schemas.carfax_with_checkout import CarfaxWithCheckoutOut

carfax_router = APIRouter()

DEFAULT_SOURCE = 'web'
CarfaxPurchasePage = create_pagination_page(CarfaxPurchaseRead)


@carfax_router.post("/carfax/buy-carfax", response_model=CarfaxWithCheckoutOut,
                    summary='Buy new carfax', description="Create buy carfax obj and get checkout link\n"
                                                          f"required permissions: {Permissions.CARFAX_OWN_WRITE.value}")
async def buy_carfax_request(
        user: HeaderUser = Depends(require_permissions(Permissions.CARFAX_OWN_WRITE)),
        data: CarfaxPurchaseIn = Body(...),
        db: AsyncSession = Depends(get_db),
        api: CarfaxAPIClient = Depends(get_carfax_client),
) -> CarfaxWithCheckoutOut:
    logger.info(
        "Starting carfax purchase request",
        extra={'vin': data.vin, 'user_external_id': user.uuid}
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
            user_external_id=user.uuid,
            source=DEFAULT_SOURCE,
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


@carfax_router.get(
    "/carfax/my",
    response_model=CarfaxPurchasePage,
    summary='Get all user carfaxes',
    description=f"Get all user carfaxes\nrequired permissions: {Permissions.CARFAX_OWN_READ.value}"
)
async def get_carfaxes(
        user: HeaderUser = Depends(require_permissions(Permissions.CARFAX_OWN_READ)),
        db: AsyncSession = Depends(get_db)
):
    logger.info("Getting carfaxes for user", extra={'user_external_id': user.uuid})

    try:
        service = CarfaxPurchasesService(db)
        stmt = service.get_all_for_user_stmt(user.uuid, DEFAULT_SOURCE)
        return await paginate(db, stmt)

    except Exception as e:
        logger.error(
            "Error getting carfaxes",
            extra={'user_external_id': user.uuid, 'error': str(e)},
            exc_info=True
        )
        raise


@carfax_router.get(
    "/carfax/{vin}",
    response_model=CarfaxPurchaseRead,
    description=f"Get carfax by VIN for user\nrequired permissions: {Permissions.CARFAX_OWN_READ.value}"
)
async def get_carfax_by_vin(
        vin: str,
        user: HeaderUser = Depends(require_permissions(Permissions.CARFAX_OWN_READ)),
        db: AsyncSession = Depends(get_db),
) -> CarfaxPurchaseRead:
    logger.info(
        "Getting carfax by VIN",
        extra={
            'vin': vin,
            'user_external_id': user.uuid,
            'endpoint': 'get_carfax_by_vin'
        }
    )

    try:
        service = CarfaxPurchasesService(db)
        carfax = await service.get_carfax_with_link(
            user_external_id=user.uuid,
            source=DEFAULT_SOURCE,
            vin=vin
        )

        return CarfaxPurchaseRead.model_validate(carfax).model_dump()

    except Exception as e:
        logger.error(
            "Error getting carfax by VIN",
            extra={
                'vin': vin,
                'user_external_id': user.uuid,
                'error': str(e),
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        raise ServerProblem(detail='Internal server error') from e
