import anyio
import pytest
from unittest.mock import AsyncMock

from httpx import AsyncClient
from fastapi import FastAPI
from pydantic import HttpUrl

from api.carfax_api import CarfaxAPIClient
from api.types import CheckBalanceOut, CarfaxOut
from database.crud.carfax_purchases import CarfaxPurchasesService
from database.schemas.carfax_purchases import CarfaxPurchaseCreate
from schemas import CarfaxPurchaseIn

# --- constants ---------------------------------------------------------------
EXTERNAL_ID_1 = "100"
EXTERNAL_ID_2 = "200"
SOURCE = "web"
VIN = "1HGBH41JXMN109186"
LINK = "https://example.com/report.pdf"

# --- fixtures ----------------------------------------------------------------
@pytest.fixture
def mock_carfax_client(app: FastAPI) -> AsyncMock:
    """Единый мок Carfax-клиента для всех тестов."""
    client = AsyncMock(spec=CarfaxAPIClient)
    client.check_balance.return_value = CheckBalanceOut(balance=2)

    app.dependency_overrides[CarfaxAPIClient] = lambda: client
    yield client
    app.dependency_overrides.clear()


# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_two_webhooks_same_vin_call_external_only_once(
    client: AsyncClient,
    db,
    mock_carfax_client: AsyncMock,
) -> None:
    """
    Два webhook-запроса (paid) по двум разным покупкам,
    но одному VIN → внешний Carfax вызывается ровно один раз,
    а ссылка в обеих записях одинаковая.
    """
    p1 = await CarfaxPurchasesService(db).create(
        CarfaxPurchaseCreate(user_external_id=EXTERNAL_ID_1, source=SOURCE, vin=VIN)
    )
    p2 = await CarfaxPurchasesService(db).create(
        CarfaxPurchaseCreate(user_external_id=EXTERNAL_ID_2, source=SOURCE, vin=VIN)
    )

    mock_carfax_client.get_carfax.return_value = CarfaxOut(
        status="success",
        file=HttpUrl(LINK),
    )

    resp1 = await client.post(f"/internal/carfax/webhook/{p1.id}/paid")
    resp2 = await client.post(f"/internal/carfax/webhook/{p2.id}/paid")

    assert resp1.status_code == resp2.status_code == 200
    assert resp1.json()["link"] == LINK
    assert resp2.json()["link"] == LINK
    assert mock_carfax_client.get_carfax.call_count == 1
    mock_carfax_client.check_balance.assert_not_called()


@pytest.mark.asyncio
async def test_get_carfax_link_already_in_another_record(
    client: AsyncClient,
    db,
    mock_carfax_client: AsyncMock,
) -> None:
    """
    У пользователя есть оплаченная запись без ссылки.
    В базе уже существует другая запись с тем же VIN и готовой ссылкой.
    При GET /carfax/{vin}/ ссылка должна скопироваться из БД,
    а внешний Carfax не должен вызываться.
    """
    # донор
    await CarfaxPurchasesService(db).create(
        CarfaxPurchaseCreate(
            user_external_id=EXTERNAL_ID_1,
            source=SOURCE,
            vin=VIN,
            link=LINK,
            is_paid=True,
        )
    )
    # реципиент
    await CarfaxPurchasesService(db).create(
        CarfaxPurchaseCreate(
            user_external_id=EXTERNAL_ID_2,
            source=SOURCE,
            vin=VIN,
            link=None,
            is_paid=True,
        )
    )

    mock_carfax_client.get_carfax.return_value = CarfaxOut(
        status="success",
        file=HttpUrl(LINK),
    )

    params = {"user_external_id": EXTERNAL_ID_2, "source": SOURCE}
    resp = await client.get(f"/carfax/{VIN}/", params=params)

    assert resp.status_code == 200
    assert resp.json()["link"] == LINK           # ссылка взята из БД
    mock_carfax_client.get_carfax.assert_not_awaited()
    mock_carfax_client.check_balance.assert_not_called()





