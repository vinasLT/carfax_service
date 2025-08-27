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
        logger.debug("StripeClient instance created")

    async def connect(self):
        try:
            logger.info("Attempting to connect to payment service", extra={
                'service_url': settings.PAYMENT_SERVICE_RPC_URL
            })

            self.channel = grpc.aio.insecure_channel(settings.PAYMENT_SERVICE_RPC_URL)
            self.stub = stripe_pb2_grpc.StripeServiceStub(self.channel)

            logger.info("Successfully connected to payment service")

        except Exception as e:
            logger.error("Failed to connect to payment service", extra={
                'error': str(e),
                'service_url': settings.PAYMENT_SERVICE_RPC_URL
            })
            raise

    async def disconnect(self):
        if self.channel:
            try:
                logger.info("Disconnecting from payment service")
                await self.channel.close()
                logger.info("Successfully disconnected from payment service")
            except Exception as e:
                logger.warning("Error during disconnection from payment service", extra={
                    'error': str(e)
                })
        else:
            logger.debug("No active channel to disconnect")

    async def create_checkout_link(self, purpose: str, purpose_external_id: str, success_link: str,
                                   cancel_link: str, user_external_id: str,
                                   source: str) -> stripe_pb2.GetCheckoutLinkResponse:
        logger.info("Creating checkout link request", extra={
            'purpose': purpose,
            'purpose_external_id': purpose_external_id,
            'user_external_id': user_external_id,
            'source': source,
            # Не логируем полные URL для безопасности, только домены
            'success_domain': success_link.split('/')[2] if success_link.startswith('http') else 'unknown',
            'cancel_domain': cancel_link.split('/')[2] if cancel_link.startswith('http') else 'unknown'
        })

        try:
            data = stripe_pb2.GetCheckoutLinkRequest(
                purpose=purpose,
                purpose_external_id=purpose_external_id,
                success_link=success_link,
                cancel_link=cancel_link,
                user_external_id=user_external_id,
                source=source
            )

            logger.debug("Sending gRPC request to GetCheckoutLink")
            response = await self.stub.GetCheckoutLink(data)

            logger.info("Checkout link created successfully", extra={
                'purpose_external_id': purpose_external_id,
                'user_external_id': user_external_id,
                'has_link': bool(response.link)
            })

            return response

        except grpc.aio.AioRpcError as e:
            logger.error("gRPC error while creating checkout link", extra={
                'error': str(e),
                'grpc_code': e.code(),
                'grpc_details': e.details(),
                'purpose_external_id': purpose_external_id,
                'user_external_id': user_external_id
            })
            raise
        except Exception as e:
            logger.error("Unexpected error while creating checkout link", extra={
                'error': str(e),
                'error_type': type(e).__name__,
                'purpose_external_id': purpose_external_id,
                'user_external_id': user_external_id
            })
            raise


async def get_checkout_link(purpose_external_id: str, success_link: str, cancel_link: str,
                            user_external_id: str, source: str, purpose: str = 'CARFAX') -> Optional[str]:
    request_id = f"{user_external_id}_{purpose_external_id}"

    logger.info("Starting checkout link creation process", extra={
        "request_id": request_id,
        "purpose_external_id": purpose_external_id,
        "success_link": success_link,
        "cancel_link": cancel_link,
        "user_external_id": user_external_id,
        "source": source,
        "purpose": purpose,
    })

    stripe_client = StripeClient()

    try:
        await stripe_client.connect()

        response = await stripe_client.create_checkout_link(
            purpose, purpose_external_id, success_link, cancel_link, user_external_id, source
        )

        if response and response.link:
            logger.info("Checkout link successfully obtained", extra={
                "request_id": request_id,
                "purpose_external_id": purpose_external_id,
                "user_external_id": user_external_id,
                "link_length": len(response.link)
            })
            return response.link
        else:
            logger.warning("Checkout link response is empty", extra={
                "request_id": request_id,
                "purpose_external_id": purpose_external_id,
                "user_external_id": user_external_id
            })
            return None

    except grpc.aio.AioRpcError as e:
        logger.error("gRPC error during checkout link creation", extra={
            "request_id": request_id,
            "error": str(e),
            "grpc_code": e.code().name,
            "grpc_details": e.details(),
            "purpose_external_id": purpose_external_id,
            "user_external_id": user_external_id
        })
        return None

    except Exception as e:
        logger.error("Unexpected error during checkout link creation", extra={
            "request_id": request_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "purpose_external_id": purpose_external_id,
            "user_external_id": user_external_id
        })
        return None

    finally:
        try:
            await stripe_client.disconnect()
            logger.debug("Checkout link creation process completed", extra={
                "request_id": request_id
            })
        except Exception as e:
            logger.error("Error during cleanup", extra={
                "request_id": request_id,
                "error": str(e)
            })