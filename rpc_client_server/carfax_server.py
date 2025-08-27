import traceback

import grpc

from api.carfax_api import CarfaxAPIClient
from core.logger import logger
from database import get_db
from database.crud.carfax_purchases import CarfaxPurchasesService
from database.schemas.carfax_purchases import CarfaxPurchaseReadWithoutId
from rpc_client_server.gen.python.carfax.v1 import carfax_pb2_grpc, carfax_pb2





class CarfaxRpc(carfax_pb2_grpc.CarfaxServiceServicer):

    async def BuyCarfax(self, request: carfax_pb2.BuyCarfaxRequest, context):
        try:
            api = CarfaxAPIClient()

            balance = await api.check_balance()
            if balance.balance <= 1:
                logger.error("Insufficient carfax balance", extra={'balance': balance.balance})

                context.set_code(grpc.StatusCode.RESOURCE_EXHAUSTED)
                context.set_details('Low carfax api balance')
                return carfax_pb2.BuyCarfaxResponse()
            is_exist = await api.check_if_vin_exists(vin=request.vin)
            if not is_exist:
                logger.warning("VIN not found", extra={'vin': request.vin})

                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details('VIN not found')
                return carfax_pb2.BuyCarfaxResponse()

            async with get_db() as db:
                carfax_service = CarfaxPurchasesService(db)

                carfax, link = await carfax_service.create_purchase_with_checkout(
                    user_external_id=request.user_external_id,
                    source=request.source,
                    vin=request.vin,
                    success_link=request.success_url,
                    cancel_link=request.cancel_url
                )

                logger.info(
                    "Carfax purchase request completed",
                    extra={'carfax_id': carfax.id, 'vin': request.vin}
                )

                carfax = carfax_pb2.Carfax(**CarfaxPurchaseReadWithoutId.model_validate(carfax).model_dump(mode="json", exclude_none=True))
                return carfax_pb2.BuyCarfaxResponse(carfax=carfax, link=link)

        except Exception as e:
            print(traceback.format_exc())
            logger.error(
                "Error in carfax purchase",
                extra={'vin': request.vin, 'error': str(e)},
                exc_info=True
            )
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal error')
            return carfax_pb2.BuyCarfaxResponse()

    async def GetAllCarfaxesForUser(self, request: carfax_pb2.GetAllCarfaxesForUserRequest, context):
        try:
            async with get_db() as db:
                carfax_service = CarfaxPurchasesService(db)
                carfaxes = await carfax_service.get_all_for_user(request.user_external_id, request.source)

                rpc_carfaxes = [carfax_pb2.Carfax(**CarfaxPurchaseReadWithoutId.model_validate(carfax).
                                                  model_dump(mode='json', exclude_none=True)) for carfax in carfaxes]
                return carfax_pb2.GetAllCarfaxesForUserResponse(carfaxes=rpc_carfaxes)
        except Exception as e:
            logger.error(
                "Error while retrieving carfaxes for user",
                extra={'user_id': request.user_external_id, 'error': str(e)},
                exc_info=True
            )
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal error')
            return carfax_pb2.GetCarfaxByVinResponse()

    async def GetCarfaxByVin(self, request: carfax_pb2.GetCarfaxByVinRequest, context):
        try:
            async with get_db() as db:
                vin = request.vin.upper()

                service = CarfaxPurchasesService(db)
                carfax = await service.get_carfax_with_link(
                    user_external_id=request.user_external_id,
                    source=request.source,
                    vin=vin
                )
                if not carfax:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details('VIN not found')
                    return carfax_pb2.GetCarfaxByVinResponse()
                carfax = CarfaxPurchaseReadWithoutId.model_validate(carfax).model_dump(mode="json", exclude_none=True)
                rcp_carfax = carfax_pb2.Carfax(**carfax)

                return carfax_pb2.GetCarfaxByVinResponse(carfax=rcp_carfax)
        except Exception as e:

            logger.error(
                "Error while retrieving carfax by VIN",
                extra={'vin': request.vin, 'error': str(e)},
                exc_info=True
            )
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal error')
            return carfax_pb2.GetCarfaxByVinResponse()

    async def IsVinExists(self, request: carfax_pb2.IsVinExistsRequest, context) -> carfax_pb2.IsVinExistsResponse:
        logger.debug("Checking if VIN exists", extra={'vin': request.vin})
        try:
            api = CarfaxAPIClient()
            is_exists = await api.check_if_vin_exists(vin=request.vin)
            return carfax_pb2.IsVinExistsResponse(is_exists=is_exists)
        except Exception as e:
            logger.error(
                "Error while checking if VIN exists",
                extra={'vin': request.vin, 'error': str(e)},
                exc_info=True
            )
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal error')
            return carfax_pb2.IsVinExistsResponse()









