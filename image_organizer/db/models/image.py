from collections.abc import Iterable
from pathlib import Path
from typing import Self, overload

from sqlalchemy import select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship
from sqlalchemy.types import String

from image_organizer.db.models import Base
from image_organizer.db.models.tag import Tag


class Image(Base):
    __tablename__ = 'image'

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(), unique=True)

    tags: Mapped[list[Tag]] = relationship(
        back_populates='image',
        cascade='all, delete-orphan',
        lazy='joined'
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

    def format_path(self) -> Path:
        return self.path_formatter(self.path)

    @classmethod
    def many_from_paths(cls, paths: Iterable[Path], session: Session) -> list[Self]:
        present_in_db_query = select(cls) \
            .where(Image.path.in_(map(Image.path_formatter, paths)))

        present_in_db = session.scalars(present_in_db_query).unique().all()
        already_loaded_paths = set(map(
            lambda image: image.format_path(),
            present_in_db
        ))

        images: list[Image] = list(present_in_db)
        new_images: list[Image] = []
        for path in map(Path.absolute, paths):
            if path in already_loaded_paths:
                continue

            new_image = Image(
                path=Image.path_formatter(path)
            )

            new_images.append(new_image)

        session.add_all(new_images)
        session.commit()

        images.extend(new_images)
        return images
