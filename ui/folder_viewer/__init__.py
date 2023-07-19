from asyncio import Future
from collections.abc import Iterable
from pathlib import Path

from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QPixmap
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from image_organizer.image_utils.load_and_resize import Dimentions
from image_organizer.pixmap_cache import PixmapCache, PixmapOrFuture
from image_organizer.utils.format_strings import format_strings
from ui.folder_viewer.image_viewer import ImageViewer

DIMENTIONS_MULTIPLIER = 4


class FolderViewer(QWidget):
    def __init__(
        self,
        image_paths: Iterable[Path],
        cache: PixmapCache
    ):
        super().__init__()

        self._image_paths = list(image_paths)

        self._first_show = True
        self.is_cached = False
        self._current_index = 0

        self._cache = cache

        self.gui()

    def gui(self) -> None:
        self._layout = QVBoxLayout()

        self.setup_image_layout()
        self.setup_info_labels_layout()

        self._layout.addLayout(self.image_layout)
        self._layout.addLayout(self.info_labels_layout)

        self.setLayout(self._layout)

    def setup_image_layout(self) -> None:
        self.image_layout = QVBoxLayout()
        self.image_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._viewer = ImageViewer(
            self
        )

        self.image_number_label = QLabel()

        self.image_layout.addWidget(self._viewer)
        self.image_layout.addWidget(self.image_number_label)

    def setup_info_labels_layout(self) -> None:
        self.info_labels_layout = QVBoxLayout()

        self.image_info_label = QLabel()

        self.info_labels_layout.addWidget(self.image_info_label)

    @property
    def current_image_path(self) -> Path:
        return self._image_paths[self._current_index]

    def _load(self, image_path: Path) -> PixmapOrFuture:
        scene_rect = self.rect()
        suitable_dimentions = Dimentions(
            int(scene_rect.width() * DIMENTIONS_MULTIPLIER),
            int(scene_rect.height() * DIMENTIONS_MULTIPLIER)
        )

        return self._cache.get_or_load_pixmap(
            image_path,
            suitable_dimentions
        )


    def _update(self, pixmap: PixmapOrFuture | None) -> None:
        if isinstance(pixmap, Future):
            QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self._viewer.show_info_text('Loading...')

            def done_callback(completed_future: Future[QPixmap | None]) -> None:
                result = completed_future.result()
                if result is None:
                    return

                self._update(result)
                QGuiApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)

            pixmap.add_done_callback(done_callback)

            return

        self._viewer.setPhoto(pixmap)

        if pixmap is None:
            self.image_info_label.setText('No information about the images...')
            self.image_number_label.setText('0 / 0')

            return

        # FIXME: Move the labels to a separate component
        formatted_path = str(self.current_image_path.absolute())
        cached_string = '(cached)' if self.is_cached else None
        cache_size = 'Cache size: {kbytes:.2f} KBytes ({mbytes:.2f} MBytes)'.format(
            kbytes=self._cache.size_kbytes,
            mbytes=self._cache.size_mb
        )

        self.image_info_label.setText(
            format_strings(
                (formatted_path, cached_string),
                cache_size
            )
        )

        image_number_text = f'{self._current_index + 1} / {len(self._image_paths)}'
        self.image_number_label.setText(image_number_text)

    def switch_image(self, move_by: int, force_update: bool = False) -> None:
        if len(self._image_paths) == 0:
            self._update(None)
            return

        old_index = self._current_index
        self._current_index = max(
            min(len(self._image_paths) - 1, self._current_index + move_by),
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

        del self._image_paths[self._current_index]

        self.switch_image(0, force_update=True)

    def showEvent(self, a0: QtGui.QShowEvent):
        super().showEvent(a0)

        if not self._first_show:
            return

        first_pixmap = self._load(self.current_image_path)
        self._update(first_pixmap)
        self._first_show = False
