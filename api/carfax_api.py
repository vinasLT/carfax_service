import asyncio
import os
from typing import Literal

from httpx import AsyncClient, HTTPStatusError
from dotenv import load_dotenv
from rfc9457 import BadRequestProblem

from api.types import CarfaxOut, CheckBalanceOut

load_dotenv()

class CarfaxAPIClient:
    _HEADERS = {
        'api-key': os.getenv("CARFAX_API_TOKEN"),
    }
    _BASE_URL = 'https://api.covin.io/api/'

    def __init__(self):
        self.session = AsyncClient(timeout=10)

    async def _make_request(
        self,
        method: Literal['GET', 'POST'],
        url: str,
        data: dict = None,
        retries: int = 3,
        delay: float = 1.0
    ) -> dict:
        url = f'{self._BASE_URL}{url}'

        for attempt in range(1, retries + 1):
            try:
                response = await self.session.request(
                    method, url=url, json=data, headers=self._HEADERS
                )
                print(response.status_code)
                print(response.text)
                response.raise_for_status()
                return response.json()
            except HTTPStatusError:
                raise BadRequestProblem(
                    detail='Error while making request',
                    short_message='error_make_request'
                )
            except Exception as e:
                print(f'Attempt {attempt} failed with error: {e}')
                if attempt == retries:
                    raise BadRequestProblem(
                        detail='Error while request, not related with response status',
                        short_message='error_make_request_not_related_status'
                    )
                await asyncio.sleep(delay)
        raise BadRequestProblem(
            detail='Error while request, not related with response status',
            short_message='error_make_request_not_related_status'
        )

    async def get_carfax(self, vin: str, re_buy: bool = False)->CarfaxOut:
        data = {
            'vin': vin,
            're_buy': re_buy
        }
        response = await self._make_request(method='POST', url=f'reports/carfax', data=data)
        return CarfaxOut.model_validate(response)

    async def check_balance(self)-> CheckBalanceOut:
        response = await self._make_request(method='GET', url=f'users/balance')
        return CheckBalanceOut.model_validate(response)

    async def check_if_vin_exists(self, vin: str)->bool:
        response = await self._make_request(method='GET', url=f'reports/check/exit?vin={vin}')
        if response.get('notFound'):
            return False
        else:
            return True




if __name__ == "__main__":
    app = CarfaxAPIClient()
    async def main():
        response = await app.check_if_vin_exists('WBA8E3G54GNU00225')
        print(response)
    asyncio.run(main())
