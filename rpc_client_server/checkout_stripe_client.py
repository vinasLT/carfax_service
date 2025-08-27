import os
import sys

import grpc

from config import settings
from core.logger import logger

sys.path.append(os.path.join(os.path.dirname(__file__), 'gen/python'))

from payment.v1 import stripe_pb2, stripe_pb2_grpc

class StripeClient:
    def __init__(self):
        self.channel = None
        self.stub = None

    async def connect(self):
        self.channel = grpc.aio.insecure_channel(settings.PAYMENT_SERVICE_RPC_URL)
        self.stub = stripe_pb2_grpc.StripeServiceStub(self.channel)

    async def disconnect(self):
        if self.channel:
            await self.channel.close()

    async def create_checkout_link(self, purpose: str, purpose_external_id: str, success_link: str, cancel_link: str,
                                   user_external_id: str,
                                   source: str) -> stripe_pb2.GetCheckoutLinkResponse:
        try:
            data = stripe_pb2.GetCheckoutLinkRequest(
                purpose=purpose,
                purpose_external_id=purpose_external_id,
                success_link=success_link,
                cancel_link=cancel_link,
                user_external_id=user_external_id,
                source=source
            )
            return await self.stub.GetCheckoutLink(data)
        except grpc.aio.AioRpcError as e:
            logger.error(f"Error while creating checkout link: {e}")
            raise


async def get_checkout_link(purpose_external_id: str, success_link: str, cancel_link: str,
                           user_external_id: str, source: str, purpose: str = 'CARFAX') -> str:
    stripe_client = StripeClient()
    await stripe_client.connect()
    try:
        response = await stripe_client.create_checkout_link(
            purpose, purpose_external_id, success_link, cancel_link, user_external_id, source
        )
        return response.link
    except grpc.aio.AioRpcError as e:
        logger.error(f"Error while creating checkout link: {e}")
    finally:
        await stripe_client.disconnect()