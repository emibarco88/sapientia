from sqlalchemy import create_engine
from sapientia.config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False, future=True)


def get_engine():
    return engine