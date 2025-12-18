from typing import Any, AsyncGenerator

from api.carfax_api import CarfaxAPIClient


async def get_carfax_client() -> AsyncGenerator[CarfaxAPIClient, Any]:
    yield CarfaxAPIClient()