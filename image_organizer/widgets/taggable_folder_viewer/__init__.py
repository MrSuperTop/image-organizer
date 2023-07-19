from collections.abc import Iterable
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from sqlalchemy import select

from image_organizer.db import session
from image_organizer.db.models.image import Image
from image_organizer.pixmap_cache import PixmapCache, PixmapOrFuture
from image_organizer.widgets.taggable_folder_viewer.control_buttons_group import (
    ControlButtonsGroup,
)
from image_organizer.widgets.taggable_folder_viewer.tags_list import TagsList
from ui.folder_viewer import FolderViewer


class TaggableFolderViewer(FolderViewer):
    image_changed = pyqtSignal(Image)

    def __init__(
        self,
        image_paths: Iterable[Path],
        move_to: Path,
        cache: PixmapCache
    ) -> None:
        self.set_images(image_paths)

        super().__init__(
            image_paths,
            cache
        )

        self._move_to = move_to

    def gui(self) -> None:
        super().gui()

        self.control_buttons = ControlButtonsGroup(
            self
        )

        self._layout.addWidget(self.control_buttons)

    @property
    def tags_list(self) -> TagsList:
        return self.control_buttons.tags_list

    # TODO: Consider implementing this into the FolderViewer
    def set_images(self, paths: Iterable[Path]) -> None:
        previously_loaded_query = select(Image) \
            .where(Image.path.in_(map(Image.path_formatter, paths)))

        previously_loaded_images = session.scalars(previously_loaded_query).all()
        already_loaded_paths = set(map(
            lambda image: Image.path_formatter(image.path),
            previously_loaded_images
        ))

        self.images: list[Image] = list(previously_loaded_images)
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

        self.images.extend(new_images)

    @property
    def move_to(self):
        return self._move_to

    @move_to.setter
    def move_to(self, new_move_to: Path) -> None:
        self._move_to = new_move_to

    @property
    def current_image(self) -> Image:
        return self.images[self._current_index]

    def _load(self, image_path: Path) -> PixmapOrFuture:
        loaded = super()._load(image_path)

        self.image_changed.emit(self.current_image)
        return loaded
