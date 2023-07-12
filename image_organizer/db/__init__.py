from __future__ import annotations

from sqlalchemy.orm import Session

from image_organizer.db.engine import engine
from image_organizer.db.models import Base


def create_schema():
    from image_organizer.db.models.image import Image as Image

    Base.metadata.create_all(engine)

session = Session(engine)
