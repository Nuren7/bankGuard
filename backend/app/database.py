from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return "postgresql+psycopg2://" + database_url[len("postgres://") :]
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + database_url[len("postgresql://") :]
    return database_url


database_url = normalize_database_url(settings.DATABASE_URL)
connect_args = {}
engine_options = {"pool_pre_ping": True}
if database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    engine_options.pop("pool_pre_ping")
    if database_url in {"sqlite://", "sqlite:///:memory:"}:
        engine_options["poolclass"] = StaticPool
else:
    engine_options.update(
        pool_size=1,
        max_overflow=0,
        pool_timeout=30,
        pool_recycle=1800,
    )

engine = create_engine(database_url, connect_args=connect_args, **engine_options)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
