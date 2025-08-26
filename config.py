from enum import Enum

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"

class Settings(BaseSettings):
    # Application
    APP_NAME: str = 'carfax-service'
    DEBUG: bool = True
    ROOT_PATH: str = ''
    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    @property
    def enable_docs(self) -> bool:
        return self.ENVIRONMENT in [Environment.DEVELOPMENT]

    # rabbitmq
    RABBITMQ_URL: str = 'amqp://guest:guest@localhost:5672/'
    RABBITMQ_EXCHANGE_NAME: str = 'events'
    RABBITMQ_QUEUE_NAME: str = 'carfax'

    # rpc servers
    PAYMENT_SERVICE_RPC_URL: str = "localhost:50053"
    GRPC_SERVER_PORT: int = 50052

    SUCCESS_PAYMENT_URL: str = 'https://example.com/success'
    COMPANY_LINK: str = 'https://example.com'

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "test_db"
    DB_USER: str = "postgres"
    DB_PASS: str = "testpass"

settings = Settings()