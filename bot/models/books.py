from sqlalchemy import BigInteger, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(Text)
    chapters_cnt: Mapped[int] = mapped_column(Integer)
    current_chapter: Mapped[int] = mapped_column(Integer, default=0)
    user_id: Mapped[int] = mapped_column(BigInteger)
