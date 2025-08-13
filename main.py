import uvicorn
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from config import settings
from exeptions import BadRequestException
from routers import carfax_router


def create_app() -> FastAPI:
    docs_url = "/docs" if settings.enable_docs else None
    redoc_url = "/redoc" if settings.enable_docs else None
    openapi_url = "/openapi.json" if settings.enable_docs else None

    app = FastAPI(title='Carfax Service',
                  description='Carfax Service API',
                  version='0.0.1',
                  root_path=settings.ROOT_PATH,
                  docs_url=docs_url,
                  redoc_url=redoc_url,
                  openapi_url=openapi_url,
                  )

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




