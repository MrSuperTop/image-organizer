from pathlib import Path

from PyQt6.QtGui import QPixmap, QPixmapCache

DEFAULT_CACHE_LIMIT = 1024 * 1024 # 1GB


def pixmap_size_bytes(pixmap: QPixmap) -> int:
    return int((pixmap.height() * pixmap.width() * pixmap.depth()) / 8)


class PixmapCache:
    def __init__(self) -> None:
        super().__init__()

        self._qt_cache = QPixmapCache()
        self._qt_cache.setCacheLimit(DEFAULT_CACHE_LIMIT)
        self._size = 0

    def _format_key(self, key: Path) -> str:
        return str(key.absolute())

    def get(self, key: Path) -> QPixmap | None:
        entry: QPixmap | None = self._qt_cache.find(self._format_key(key))
        return entry

    def insert(self, key: Path, value: QPixmap) -> None:
        self._size += pixmap_size_bytes(value)

        self._qt_cache.insert(self._format_key(key), value)

    def delete(self, key: Path) -> bool:
        removed = self.get(key)
        if removed is None:
            return False

        self._size -= pixmap_size_bytes(removed)

        self._qt_cache.remove(self._format_key(key))
        return True

    @property
    def size_kbytes(self) -> float:
        return self._size / 1024

    @property
    def size_mb(self) -> float:
        return self._size / 1024 ** 2
