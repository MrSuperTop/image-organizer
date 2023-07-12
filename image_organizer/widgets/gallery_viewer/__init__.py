from collections.abc import Iterable
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from image_organizer.image_utils.load_and_resize import Dimentions, load_and_resize
from image_organizer.image_utils.pixmap_cache import PixmapCache
from image_organizer.utils.format_strings import format_strings
from image_organizer.utils.wait_cursor import wait_cursor
from image_organizer.widgets.gallery_viewer.image_viewer import ImageViewer


# TODO: Asyncronous image loading and possibly background tasks for loading beforehand
class GalleryViewer(QWidget):
    def __init__(
        self,
        image_paths: Iterable[Path],
        max_image_dimentions: Dimentions
    ):
        super().__init__()

        self.max_dimentions = max_image_dimentions
        self.image_paths = list(image_paths)

        self.is_cached = False
        self._current_index = 0
        self._cache = PixmapCache()

        self.gui()

        first_pixmap = self._load(self.current_image_path)
        if first_pixmap is None:
            # TODO: Error message?
            raise Exception('Could not load the first pixmap')

        self._update(first_pixmap)


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
        return self.image_paths[self._current_index]

    def _load(self, image_path: Path) -> QPixmap | None:
        cached = self._cache.get(image_path)
        self.is_cached = False

        if cached is not None:
            self.is_cached = True
            return cached

        pixmap = load_and_resize(image_path, self.max_dimentions)

        if pixmap is not None:
            self._cache.insert(image_path, pixmap)

        return pixmap

    def _update(self, pixmap: QPixmap | None) -> None:
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

        image_number_text = f'{self._current_index + 1} / {len(self.image_paths)}'
        self.image_number_label.setText(image_number_text)

    def switch_image(self, move_by: int, force_update: bool = False) -> bool:
        if len(self.image_paths) == 0:
            self._update(None)

            return True

        old_index = self._current_index
        self._current_index = max(
            min(len(self.image_paths) - 1, self._current_index + move_by),
            0
        )

        if old_index == self._current_index and not force_update:
            return False

        with wait_cursor():
            self._pixmap = self._load(self.current_image_path)

        if self._pixmap is None:
            return False

        self._update(self._pixmap)
        return True

    def next(self) -> bool:
        return self.switch_image(1)

    def prev(self) -> bool:
        return self.switch_image(-1)

    def clear_and_switch(self) -> None:
        self._cache.delete(self.current_image_path)
        del self.image_paths[self._current_index]

        self.switch_image(0, force_update=True)
