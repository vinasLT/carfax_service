from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from api.carfax_api import CarfaxAPIClient
from exeptions import BadRequestException
from routers import carfax_router

api: CarfaxAPIClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global api
    api = CarfaxAPIClient()
    yield

def create_app() -> FastAPI:
    app = FastAPI()

    @app.exception_handler(BadRequestException)
    async def bad_request_exception_handler(request: Request, exc: BadRequestException):
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message, "code": exc.short_message},
        )

    app.include_router(carfax_router)
    return app

app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8001)




