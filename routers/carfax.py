from fastapi import APIRouter, Body, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.carfax_api import CarfaxAPIClient
from database import get_db
from database.crud.carfax_purchases import CarfaxPurchasesService
from database.schemas.carfax_purchases import CarfaxPurchaseRead, CarfaxPurchaseCreate, CarfaxPurchaseUpdate
from exeptions import BadRequestException
from schemas import CarfaxPurchaseIn

carfax_router = APIRouter()



@carfax_router.post("/carfax/buy-carfax", response_model=CarfaxPurchaseRead)
async def buy_carfax_request(
    data: CarfaxPurchaseIn = Body(...),
    db: AsyncSession = Depends(get_db),
    api: CarfaxAPIClient = Depends(),
)-> CarfaxPurchaseRead:
    response = await api.check_balance()
    print(response)
    if response.balance <= 1:
        raise BadRequestException(message='No carfaxes left, admin need to top up his account',
                                  short_message='top_up_needed')

    service = CarfaxPurchasesService(db)
    carfax = await service.get_vin_for_user(external_user_id=data.user_external_id,
                                            source=data.source, vin=data.vin)
    print(carfax)
    if not carfax:
        carfax = await service.create(CarfaxPurchaseCreate(user_external_id=data.user_external_id,
                                                  source=data.source,
                                                  vin=data.vin.upper()))
    return CarfaxPurchaseRead.model_validate(carfax).model_dump()

@carfax_router.post('/internal/carfax/webhook/{carfax_id}/paid', response_model=CarfaxPurchaseRead)
async def carfax_paid(carfax_id: int, db: AsyncSession = Depends(get_db), api:CarfaxAPIClient = Depends()) -> CarfaxPurchaseRead:
    service = CarfaxPurchasesService(db)
    carfax = await service.get(carfax_id)
    already_in_db = await service.get_by_vin(vin=carfax.vin)

    link = already_in_db.link if already_in_db else None
    if link is None:
        carfax_api = await api.get_carfax(carfax.vin)
        link = str(carfax_api.file)
    await service.update(carfax.id, CarfaxPurchaseUpdate(link=link, is_paid=True))
    return CarfaxPurchaseRead.model_validate(carfax).model_dump()

@carfax_router.get("/carfax", response_model=list[CarfaxPurchaseRead])
async def get_carfaxes(user_external_id: str = Query(...),
                     source: str = Query(...), db: AsyncSession = Depends(get_db)):
    service = CarfaxPurchasesService(db)
    return await service.get_all_for_user(user_external_id, source)

@carfax_router.get("/carfax/{vin}/", response_model=CarfaxPurchaseRead)
async def get_carfax_by_vin(vin:str, user_external_id: str = Query(...), source: str = Query(...),
                            db: AsyncSession = Depends(get_db),
                            api:CarfaxAPIClient = Depends())-> CarfaxPurchaseRead:
    service = CarfaxPurchasesService(db)
    carfax = await service.get_vin_for_user(
        external_user_id=user_external_id, source=source, vin=vin
    )
    if not carfax:
        raise HTTPException(status_code=404, detail="Carfax not found")

    if carfax.is_paid and not carfax.link:
        already_in_db = await service.get_by_vin(vin=carfax.vin)
        if already_in_db and already_in_db.link:
            carfax = await service.update(
                carfax.id, CarfaxPurchaseUpdate(link=already_in_db.link)
            )
        else:
            carfax_api = await api.get_carfax(carfax.vin)
            carfax = await service.update(
                carfax.id, CarfaxPurchaseUpdate(link=str(carfax_api.file))
            )
    return CarfaxPurchaseRead.model_validate(carfax).model_dump()