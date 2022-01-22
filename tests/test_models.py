from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from bot_config import db_user, db_password
from models.road import PomodoroStats

engine = create_engine(
    f'postgresql://{db_user}:{db_password}@localhost:5432/bot')


def connect_db():
    Session = sessionmaker(bind=engine)
    return Session()


def test_connect_db():
    session = connect_db()
    session.query(PomodoroStats).all()


def test_saving_values():
    Session = sessionmaker(bind=engine)

    with Session.begin() as session:
        user = session.query(PomodoroStats).first()
        user.total_cnt = 12222

    with Session.begin() as session:
        user = session.query(PomodoroStats).first()
        assert user.total_cnt == 12222
