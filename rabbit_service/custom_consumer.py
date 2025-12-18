import json
from enum import Enum

from aio_pika.abc import AbstractIncomingMessage

from api.carfax_api import CarfaxAPIClient
from core.logger import logger
from database.crud.carfax_purchases import CarfaxPurchasesService
from database.schemas.carfax_purchases import CarfaxPurchaseUpdate
from rabbit_service.base import RabbitBaseService

class CarfaxRoutingKey(str, Enum):
    CARFAX_PURCHASE_SUCCESS = 'payment.success.carfax'


class RabbitCarfaxConsumer(RabbitBaseService):

    async def process_message(self, message: AbstractIncomingMessage):
        message_data = message.body.decode("utf-8")
        payload = json.loads(message_data).get("payload")
        routing_key = message.routing_key

        logger.info("Received new message", extra={"payload": payload})

        user_uuid = payload.get("user_uuid")
        purpose_external_id = payload.get("purpose_external_id")

        logger.info("Processing carfax payment", extra={
            "routing_key": routing_key,
            "user_uuid": user_uuid,
        })

        try:
            CarfaxRoutingKey(routing_key)
        except ValueError as e:
            logger.error("Invalid carfax routing key", extra={
                "routing_key": routing_key,
                "error": str(e)
            })
            raise

        carfax_service = CarfaxPurchasesService(self.db)
        api_client = CarfaxAPIClient()
        if not purpose_external_id.isdigit():
            logger.error("Invalid purpose external id", extra={
                "purpose_external_id": purpose_external_id
            })
            return

        carfax = await carfax_service.get(int(purpose_external_id))

        link = carfax.link
        if not link:
            existing = await carfax_service.get_by_vin(vin=carfax.vin)
            if existing:
                link = existing.link
            else:
                carfax_api = await api_client.get_carfax(carfax.vin)
                link = str(carfax_api.file)
        await carfax_service.update(carfax.id, CarfaxPurchaseUpdate(link=link, is_paid=True))










