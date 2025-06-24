import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("CARFAX_DB_HOST")
DB_PORT = os.getenv("CARFAX_DB_PORT")
DB_USER = os.getenv("CARFAX_DB_USER")
DB_PASSWORD = os.getenv("CARFAX_DB_PASS")
DB_NAME = os.getenv("CARFAX_DB_NAME")