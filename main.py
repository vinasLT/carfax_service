from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Depends, Query
from starlette.responses import JSONResponse

from api.carfax_api import CarfaxAPIClient
from api.types import CarfaxOut
from database.crud.carfax_purchases import CarfaxPurchasesService
from database.schemas.carfax_purchases import CarfaxPurchaseCreate, CarfaxPurchaseRead
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

@app.post("/internal/carfax/buy-carfax", response_model=CarfaxOut)
async def get_by_lot_id_or_vin(
    data: CarfaxPurchaseIn = Depends(),

):
    response = await api.check_balance()
    if response.balance <= 1:
        raise BadRequestException(message='No carfaxes left, admin need to top up his account',
                                  short_message='top_up_needed')
    async with CarfaxPurchasesService() as service:
        already_in_db = await service.get_by_vin(vin=data.vin)
        if not already_in_db:
            response = await api.get_carfax(data.vin)
            link = response.file
        else:
            link = already_in_db.link

        await service.create(CarfaxPurchaseCreate(user_external_id=data.user_external_id,
                                                  source=data.source,
                                                  vin=data.vin,
                                                  link=link))
    return response





@app.get("/carfax", response_model=list[CarfaxPurchaseRead])
async def get_carfax(external_user_id: str = Query(...),
                     source: str = Query(...), ):
    async with CarfaxPurchasesService() as service:
        return await service.get_all_for_user(external_user_id, source)




if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)




