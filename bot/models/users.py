from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base

from bot_config import engine

Base = declarative_base()


class Users(Base):
    __tablename__ = 'reminds'

    user_id = Column(Integer, primary_key=True)


Users.__table__.create(bind=engine, checkfirst=True)
