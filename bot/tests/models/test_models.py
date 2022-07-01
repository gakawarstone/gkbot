from sqlalchemy.orm import sessionmaker

from settings import engine
from models.road import PomodoroStats


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


def test_representation():
    Session = sessionmaker(bind=engine)

    with Session.begin() as session:
        user = session.query(PomodoroStats).first()
        print(user)
