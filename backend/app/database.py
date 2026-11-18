from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings 

#create sqlalchemy engine
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

#Sessionlocal for handling databasesessions per call
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#baseclass for orm-modells
Base = declarative_base()

def get_db():
  """
  A dependency that creates and closes datasessions securely per req
  """
  db = SessionLocal()
  try:
    yield db
  finally: 
    db.close()
