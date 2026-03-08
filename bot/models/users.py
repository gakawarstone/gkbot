from sqlalchemy import BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class Users(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_name: Mapped[str] = mapped_column(Text)
