from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base

from settings import engine

Base = declarative_base()


class Reminds(Base):
    __tablename__ = 'reminds'

    user_id = Column(Integer, primary_key=True)


Reminds.__table__.create(bind=engine, checkfirst=True)
