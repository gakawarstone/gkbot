import datetime
from sqlalchemy import BigInteger, Integer, Text, Time
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class PomodoroStats(Base):
    __tablename__ = "pomodorostats"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    today_cnt: Mapped[int] = mapped_column(Integer, default=0)
    total_cnt: Mapped[int] = mapped_column(Integer, default=0)


class RoadSettings(Base):
    __tablename__ = "roadsettings"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    time_focused: Mapped[datetime.time] = mapped_column(Time)
    time_relax: Mapped[datetime.time] = mapped_column(Time)


class Habits(Base):
    __tablename__ = "habits"

    habit_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(Text)
    notify_time: Mapped[datetime.time] = mapped_column(Time)
