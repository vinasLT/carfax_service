from contextlib import asynccontextmanager

import uvicorn
from aio_pika import connect_robust
from fastapi import FastAPI
from fastapi_problem.handler import new_exception_handler, add_exception_handler

from config import settings
from core.logger import logger
from database import get_db
from rabbit_service.custom_consumer import RabbitCarfaxConsumer, CarfaxRoutingKey
from routers import carfax_router


def create_app() -> FastAPI:
    docs_url = "/docs" if settings.enable_docs else None
    redoc_url = "/redoc" if settings.enable_docs else None
    openapi_url = "/openapi.json" if settings.enable_docs else None

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        logger.info(f"{settings.APP_NAME} started!")
        connection = await connect_robust(settings.RABBITMQ_URL)
        db = await get_db()

        consumer = RabbitCarfaxConsumer(connection, db, [member.value for member in CarfaxRoutingKey])
        await consumer.set_up()
        await consumer.start_consuming()
        yield

        await consumer.stop_consuming()

    app = FastAPI(title='Carfax Service',
                  description='Carfax Service API',
                  version='0.0.1',
                  root_path=settings.ROOT_PATH,
                  docs_url=docs_url,
                  redoc_url=redoc_url,
                  openapi_url=openapi_url,
                  lifespan=lifespan
                  )

    eh = new_exception_handler()
    add_exception_handler(app, eh)


    app.include_router(carfax_router, prefix="/private/v1")
    return app

app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8001)




