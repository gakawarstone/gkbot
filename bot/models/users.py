from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base

from settings import engine

Base = declarative_base()


class Users(Base):
    __tablename__ = 'reminds'

    user_id = Column(Integer, primary_key=True)


Users.__table__.create(bind=engine, checkfirst=True)
