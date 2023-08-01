from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from PyQt6.QtGui import QPixmap

from image_organizer.image_utils.load_and_resize import Dimentions


@dataclass()
class CacheEntry:
    pixmap: QPixmap
    dimentions: Dimentions
    image_path: Path
    added_at: datetime = field(default_factory=datetime.now)

    def pixmap_size_bytes(self) -> int:
        return int(
            self.pixmap.height() * self.pixmap.width() * self.pixmap.depth() / 8
        )
