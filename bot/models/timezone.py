import datetime as dt
from sqlalchemy import BigInteger, Interval
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class TimeZone(Base):
    __tablename__ = "timezone"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tz: Mapped[dt.timedelta] = mapped_column(Interval)
