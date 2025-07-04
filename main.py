from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Depends, Query
from starlette.responses import JSONResponse

from api.carfax_api import CarfaxAPIClient
from database.crud.carfax_purchases import CarfaxPurchasesService
from database.schemas.carfax_purchases import CarfaxPurchaseCreate, CarfaxPurchaseRead, CarfaxPurchaseUpdate
from exeptions import BadRequestException
from schemas import CarfaxPurchaseIn

api: CarfaxAPIClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global api
    api = CarfaxAPIClient()
    yield

app = FastAPI(lifespan=lifespan)

@app.exception_handler(BadRequestException)
async def bad_request_exception_handler(request: Request, exc: BadRequestException):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message, "code": exc.short_message},
    )

@app.post("/carfax/buy-carfax", response_model=CarfaxPurchaseRead)
async def buy_carfax_request(
    data: CarfaxPurchaseIn = Depends(),
)-> CarfaxPurchaseRead:
    response = await api.check_balance()
    if response.balance <= 1:
        raise BadRequestException(message='No carfaxes left, admin need to top up his account',
                                  short_message='top_up_needed')
    async with CarfaxPurchasesService() as service:
        already_in_db = await service.get_by_vin(vin=data.vin)
        link = already_in_db.link if already_in_db else None
        carfax = await service.create(CarfaxPurchaseCreate(user_external_id=data.user_external_id,
                                                  source=data.source,
                                                  vin=data.vin,
                                                  link=link))
    return CarfaxPurchaseRead.model_validate(carfax).model_dump()

@app.post('/internal/carfax/webhook/{carfax_id}/paid', response_model=CarfaxPurchaseRead)
async def carfax_paid(carfax_id: int) -> CarfaxPurchaseRead:
    async with CarfaxPurchasesService() as service:
        carfax = await service.get(carfax_id)
        if carfax.link is None:
            carfax_api = await api.get_carfax(carfax.vin)
            await service.update(carfax.id, CarfaxPurchaseUpdate(link=str(carfax_api.file)))
    return CarfaxPurchaseRead.model_validate(carfax).model_dump()

@app.get("/carfax", response_model=list[CarfaxPurchaseRead])
async def get_carfaxes(external_user_id: str = Query(...),
                     source: str = Query(...), ):
    async with CarfaxPurchasesService() as service:
        return await service.get_all_for_user(external_user_id, source)

@app.get("/carfax/{vin}/", response_model=CarfaxPurchaseRead)
async def get_carfax_by_vin(vin:str, external_user_id: str = Query(...), source: str = Query(...))-> CarfaxPurchaseRead:
    async with CarfaxPurchasesService() as service:
        carfax = await service.get_by_vin(vin)
        if carfax.external_user_id == external_user_id and carfax.source == source:
            if carfax.is_paid and not carfax.link:
                carfax_api = await api.get_carfax(carfax.vin)
                carfax = await service.update(carfax.id, CarfaxPurchaseUpdate(link=str(carfax_api.file)))
    return CarfaxPurchaseRead.model_validate(carfax).model_dump()


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8001)




