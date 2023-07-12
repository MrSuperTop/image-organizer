from __future__ import annotations

import typing

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.types import Boolean, String

from image_organizer.db.models import Base

if typing.TYPE_CHECKING:
    from image_organizer.db.models.image import Image


class Tag(Base):
    __tablename__ = 'tag'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String())
    image_id: Mapped[int] = mapped_column(ForeignKey('image.id'))
    is_selected: Mapped[bool] = mapped_column(Boolean(), default=False)

    image: Mapped[Image] = relationship(
        back_populates='tags'
    )

    __table_args__ = (
        UniqueConstraint('image_id', 'name', name='_unique_image_pair'),
    )