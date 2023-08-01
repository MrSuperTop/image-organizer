from __future__ import annotations

import typing

from PyQt6.QtCore import pyqtBoundSignal
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from image_organizer.pixmap_cache import PixmapCache
from image_organizer.utils.format_strings import format_strings

if typing.TYPE_CHECKING:
    from ui.folder_viewer import ImageChangedData


class InfoLabels(QWidget):
    def __init__(
        self,
        cache: PixmapCache,
        image_changed_signal: pyqtBoundSignal,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.cache = cache
        image_changed_signal.connect(self._image_changed_handler)

        self.gui()

    def gui(self) -> None:
        self._layout = QVBoxLayout()

        self.image_number = QLabel()
        self.image_info = QLabel()

        self._layout.addWidget(self.image_number)
        self._layout.addWidget(self.image_info)

        self.setLayout(self._layout)

    def _set_empty(self) -> None:
        self.image_info.setText('No information about the images...')
        self.image_number.setText('0 / 0')

    def update_labels(self, changed_data: ImageChangedData) -> None:
        formatted_path = changed_data.image.path

        # TODO: Add a "loaded in X s" when the image was not cached
        cached_string = '(cached)' if changed_data.is_cached else None
        cache_size = 'Cache size: {kbytes:.2f} KBytes ({mbytes:.2f} MBytes)'.format(
            kbytes=self.cache.size_kbytes,
            mbytes=self.cache.size_mb
        )

        self.image_info.setText(
            format_strings(
                (formatted_path, cached_string),
                cache_size
            )
        )

        image_number_text = f'{changed_data.current_index + 1} / {changed_data.total_images}'
        self.image_number.setText(image_number_text)


    def _image_changed_handler(self, changed_data: ImageChangedData) -> None:
        if changed_data.pixmap is None:
            self._set_empty()
            return

        self.update_labels(changed_data)
