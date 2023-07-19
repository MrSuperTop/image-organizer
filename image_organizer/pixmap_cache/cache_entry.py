from dataclasses import dataclass

from PyQt6.QtGui import QPixmap

from image_organizer.image_utils.load_and_resize import Dimentions


@dataclass(frozen=True, eq=True)
class CacheEntry:
    pixmap: QPixmap
    dimentions: Dimentions

    def pixmap_size_bytes(self) -> int:
        return int(
            self.pixmap.height() * self.pixmap.width() * self.pixmap.depth() / 8
        )
