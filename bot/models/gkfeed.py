from sqlalchemy import BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class GkFeed(Base):
    __tablename__ = "gkfeed"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    login: Mapped[str] = mapped_column(Text)
    password: Mapped[str] = mapped_column(Text)
