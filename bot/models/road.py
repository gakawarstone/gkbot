from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PomodoroStats(Base):
    __tablename__ = 'pomodoro'

    user_id = Column(Integer, primary_key=True)
    today_cnt = Column(Integer)
    total_cnt = Column(Integer)

    def __repr__(self):
        return f'<PomodoroStats(user_id={self.user_id})>'
