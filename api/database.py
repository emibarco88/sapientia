from sapientia.db.connection import get_engine


def get_connection():
    engine = get_engine()
    with engine.begin() as connection:
        yield connection