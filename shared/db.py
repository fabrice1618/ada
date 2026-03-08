import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

_MYSQL_USER = os.environ.get('MYSQL_USER', 'plateforme_user')
_MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
_MYSQL_HOST = os.environ.get('MYSQL_HOST', 'mysql')
_MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
_MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'plateforme')

DATABASE_URL = (
    f"mysql+mysqldb://{_MYSQL_USER}:{_MYSQL_PASSWORD}"
    f"@{_MYSQL_HOST}:{_MYSQL_PORT}/{_MYSQL_DATABASE}?charset=utf8mb4"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
