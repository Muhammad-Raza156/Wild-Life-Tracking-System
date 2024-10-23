import os
from sqlalchemy import Column, String, Date, Time, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database
from dotenv import load_dotenv

load_dotenv()

user=os.getenv("db_user")
password=os.getenv("db_password")
dbname=os.getenv("db_name")
port=os.getenv("db_port")
host=os.getenv("db_host")



Database_URL= f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
database= Database(Database_URL)

engine=create_engine(Database_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Sighting(Base):
    __tablename__ = "sightings"
    id = Column(Integer, primary_key=True, index=True)
    species = Column(String, index=True)
    location = Column(String)
    date = Column(Date)
    time = Column(Time)

Base.metadata.create_all(bind=engine)

