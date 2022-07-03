from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

from settings import engine

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String)


Users.__table__.create(bind=engine, checkfirst=True)
