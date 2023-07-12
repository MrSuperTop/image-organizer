from collections.abc import Iterable
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QPixmap
from sqlalchemy import select

from image_organizer.db import session
from image_organizer.db.models.image import Image
from image_organizer.widgets.controlled_gallery.control_buttons_group import (
    ControlButtonsGroup,
)
from image_organizer.widgets.gallery_viewer import Dimentions, GalleryViewer


class ControlledGallery(GalleryViewer):
    image_changed = pyqtSignal(Image)

    def __init__(
        self,
        image_paths: Iterable[Path],
        max_image_dimentions: Dimentions,
        move_to: Path
    ):
        super().__init__(
            image_paths,
            max_image_dimentions
        )

        self._move_to = move_to
        self.current_image: Image | None = None

    def gui(self) -> None:
        super().gui()

        self.control_buttons = ControlButtonsGroup(
            self
        )

        self._layout.addWidget(self.control_buttons)

    @property
    def move_to(self):
        return self._move_to

    @move_to.setter
    def move_to(self, new_move_to: Path) -> None:
        self._move_to = new_move_to

    def _load(self, image_path: Path) -> QPixmap | None:
        loaded = super()._load(image_path)

        formatted_path = Image.path_formatter(image_path)

        query = select(Image).where(Image.path == formatted_path)
        predicate = session.scalars(query).one_or_none()

        if predicate is None:
            self.current_image = Image(
                path=formatted_path
            )

            session.add(self.current_image)
            session.commit()
        else:
            self.current_image = predicate

        self.image_changed.emit(self.current_image)
        return loaded
