from asyncio.futures import Future

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QStackedLayout, QWidget

from image_organizer.db.models.image import Image
from image_organizer.image_utils.load_and_resize import Dimentions
from image_organizer.image_utils.pixmap_cache import PixmapCache, PixmapOrFuture


class GalleryImage(QWidget):
    def __init__(
        self,
        max_dimentions: Dimentions,
        cache: PixmapCache,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.cache = cache
        self.max_dimentions = max_dimentions

        self.gui()

        self._pixmap: QPixmap | None = None

    def gui(self) -> None:
        self._layout = QStackedLayout()
        self._layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._image_container = QLabel()
        self._image_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_container.setFixedSize(*self.max_dimentions.size())

        self._info_label = QLabel()
        self._info_label.setFixedSize(*self.max_dimentions.size())
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info_label.setText('No image...')

        self._layout.addWidget(self._image_container)
        self._layout.addWidget(self._info_label)

        self.setLayout(self._layout)

    def _show_info(self, text: str) -> None:
        self._image_container.hide()
        self._info_label.setText(text)
        self._layout.setCurrentIndex(1)
        self._info_label.show()

    def _show_image(self, pixmap: QPixmap) -> None:
        self._info_label.hide()
        self._image_container.setPixmap(pixmap)
        self._image_container.setFixedSize(*self.max_dimentions.size())
        self._layout.setCurrentIndex(0)
        self._image_container.show()

    def _load_pixmap(self, image: Image) -> PixmapOrFuture:
        self._show_info('Loading...')

        pixmap = self.cache.get_or_load(
            image.path_formatter(image.path),
            self.max_dimentions
        )

        return pixmap

    def _rescale(self, to_rescale: QPixmap) -> QPixmap:
        if to_rescale.height() > to_rescale.width() and to_rescale.height() > self.max_dimentions.y:
            return to_rescale.scaledToHeight(self.max_dimentions.y)
        else:
            return to_rescale.scaledToWidth(self.max_dimentions.x)

    def _set_image(self, pixmap: QPixmap | None) -> None:
        if pixmap is None:
            self._show_info('Could not load')
        else:
            self._show_image(self._rescale(pixmap))

    async def set_image(self, new_image: Image) -> None:
        pixmap_or_future = self._load_pixmap(new_image)

        if isinstance(pixmap_or_future, Future):
            def set_callback(completed_future: Future[QPixmap | None]):
                self._set_image(completed_future.result())

            pixmap_or_future.add_done_callback(set_callback)
            return

        self._set_image(pixmap_or_future)
