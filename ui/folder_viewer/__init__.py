from abc import ABC
from asyncio import Future
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from PyQt6 import QtGui
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLayout, QVBoxLayout, QWidget

from image_organizer.db import session
from image_organizer.db.models.image import Image
from image_organizer.image_utils.load_and_resize import Dimentions
from image_organizer.pixmap_cache import PixmapCache, PixmapOrFuture
from image_organizer.utils.loading_cursor import loading_cursor
from ui.folder_viewer.image_viewer import ImageViewer
from ui.folder_viewer.info_labels import InfoLabels
from ui.folder_viewer.movement_buttonts import MovementButtons

DIMENTIONS_MULTIPLIER = 4


@dataclass()
class BaseImageChangedData(ABC):
    pixmap: QPixmap | None
    image: Image
    is_cached: bool
    total_images: int
    current_index: int


@dataclass()
class ImageChangedData(BaseImageChangedData):
    ...


# TODO: See the mime types, order the photos in chronological order
class FolderViewer(QWidget):
    image_changed = pyqtSignal(object)

    def __init__(
        self,
        image_paths: Iterable[Path],
        cache: PixmapCache
    ):
        super().__init__()

        self.images = Image.many_from_paths(image_paths, session)

        self._first_show = True
        self.is_cached = False
        self._current_index = 0

        self._cache = cache

        self._layout = self.gui()
        self.setLayout(self._layout)

    def gui(self) -> QLayout:
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.info_labels = InfoLabels(self._cache, self.image_changed)
        self._viewer = ImageViewer(
            self
        )

        self.movement_buttons = MovementButtons()
        self.movement_buttons.next_signal.connect(self.next)
        self.movement_buttons.prev_signal.connect(self.prev)

        layout.addWidget(self._viewer)
        layout.addWidget(self.info_labels)
        layout.addWidget(self.movement_buttons)

        return layout

    @property
    def current_image_path(self) -> Path:
        return self.current_image.format_path()

    def _load(self, image_path: Path) -> PixmapOrFuture:
        scene_rect = self.rect()
        suitable_dimentions = Dimentions(
            int(scene_rect.width() * DIMENTIONS_MULTIPLIER),
            int(scene_rect.height() * DIMENTIONS_MULTIPLIER)
        )

        self.is_cached, pixmap_or_future = self._cache.get_or_load_pixmap(
            image_path,
            suitable_dimentions
        )

        return pixmap_or_future


    @property
    def current_image(self) -> Image:
        return self.images[self._current_index]

    def _emit_image_changed(self, pixmap: QPixmap | None) -> None:
        image_changed_data = BaseImageChangedData(
            pixmap,
            self.current_image,
            self.is_cached,
            len(self.images),
            self._current_index
        )

        self.image_changed.emit(image_changed_data)

    def _update(self, pixmap: PixmapOrFuture | None) -> None:
        if isinstance(pixmap, Future):
            loading_cursor(pixmap)

            self._viewer.show_info_text('Loading...')

            def done_callback(completed_future: Future[QPixmap | None]) -> None:
                result = completed_future.result()
                if result is None:
                    return

                self._update(result)

            pixmap.add_done_callback(done_callback)

            return

        self._emit_image_changed(pixmap)
        self._viewer.setPhoto(pixmap)

    def switch_image(self, move_by: int, force_update: bool = False) -> None:
        if len(self.images) == 0:
            self._update(None)
            return

        old_index = self._current_index
        self._current_index = max(
            min(len(self.images) - 1, self._current_index + move_by),
            0
        )

        if old_index == self._current_index and not force_update:
            return

        loaded = self._load(self.current_image_path)
        self._update(loaded)


    def next(self) -> None:
        self.switch_image(1)

    def prev(self) -> None:
        self.switch_image(-1)

    def clear_and_switch(self) -> None:
        self._cache.delete(
            self.current_image_path,
        )

        self.images.pop(self._current_index)

        self.switch_image(0, force_update=True)

    def showEvent(self, a0: QtGui.QShowEvent):
        super().showEvent(a0)

        if not self._first_show:
            return

        first_pixmap = self._load(self.current_image_path)
        self._update(first_pixmap)
        self._first_show = False
