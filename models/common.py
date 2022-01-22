from sqlalchemy.orm import declarative_base

from bot_config import Session

Base = declarative_base()


class Common:
    session = Session()
