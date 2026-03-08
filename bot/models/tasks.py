import datetime as dt
from sqlalchemy import DateTime, Integer, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    datetime: Mapped[dt.datetime] = mapped_column(DateTime)
    callback: Mapped[bytes] = mapped_column(LargeBinary)
