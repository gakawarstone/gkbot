from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base

from .common import Common

Base = declarative_base()


class PomodoroStats(Base, Common):
    __tablename__ = 'pomodoro'

    user_id = Column(Integer, primary_key=True)
    today_cnt = Column(Integer)
    total_cnt = Column(Integer)

    def __repr__(self):
        return f'<PomodoroStats(user_id={self.user_id})>'

    @classmethod
    def get_user(cls, user_id: int) -> object:
        return cls.session.query(cls).filter_by(
            user_id=user_id).first()

    def increment(self, column: str) -> None:
        column = self.__getattribute__(column)
        print(column)
        column += 1
        PomodoroStats.session.commit()
        pass
