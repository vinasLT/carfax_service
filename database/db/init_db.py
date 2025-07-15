from database.db.session import sync_engine
from database.models import Base


def init_db():
    Base.metadata.create_all(bind=sync_engine)
