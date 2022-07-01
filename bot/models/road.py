from sqlalchemy import Column, Integer, String, Time
from sqlalchemy.orm import declarative_base

from settings import engine

Base = declarative_base()


class PomodoroStats(Base):
    __tablename__ = 'pomodoro'

    user_id = Column(Integer, primary_key=True)
    today_cnt = Column(Integer)
    total_cnt = Column(Integer)

    def __repr__(self):
        return f'<PomodoroStats(user_id={self.user_id})>'


class Habits(Base):
    __tablename__ = 'habits'

    habit_id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(Integer)
    name = Column(String)
    notify_time = Column(Time)

    def __repr__(self) -> str:
        return f'<Habits(name={self.name}, habit_id={self.habit_id})>'


PomodoroStats.__table__.create(bind=engine, checkfirst=True)
Habits.__table__.create(bind=engine, checkfirst=True)
