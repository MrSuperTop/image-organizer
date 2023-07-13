from pathlib import Path
from typing import overload

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import String

from image_organizer.db.models import Base
from image_organizer.db.models.tag import Tag


class Image(Base):
    __tablename__ = 'image'

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(), unique=True)

    tags: Mapped[list[Tag]] = relationship(
        back_populates='image', cascade='all, delete-orphan'
    )

    @staticmethod
    @overload
    def path_formatter(path: Path) -> str:
        ...

    @staticmethod
    @overload
    def path_formatter(path: str) -> Path:
        ...

    @staticmethod
    def path_formatter(path: Path | str) -> str | Path:
        if isinstance(path, Path):
            return str(path.absolute())
        else:
            return Path(path)
