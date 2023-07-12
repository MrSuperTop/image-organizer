from pathlib import Path

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import String

from image_organizer.db.models import Base
from image_organizer.db.models.tag import Tag


class Image(Base):
    __tablename__ = 'image'

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String())

    tags: Mapped[list[Tag]] = relationship(
        back_populates='image', cascade='all, delete-orphan'
    )

    @staticmethod
    def path_formatter(path: Path) -> str:
        return str(path.absolute())
