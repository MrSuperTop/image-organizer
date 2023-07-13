import asyncio
from asyncio import Future
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Concatenate, ParamSpec, TypeVar

from PyQt6.QtGui import QPixmap, QPixmapCache

from image_organizer.image_utils.load_and_resize import Dimentions, load_and_resize

DEFAULT_CACHE_LIMIT = 1024 * 1024 # 1GB
MAX_LOAD_WORKERS = 128

PixmapOrFuture = QPixmap | Future[QPixmap | None]

T = TypeVar('T')
WrappedSpec = ParamSpec('WrappedSpec')
RT = TypeVar('RT')


# TODO: Convert into a decorator or find a plug-n-play solution
def get_generic_callback(
    wrapped: Callable[Concatenate[T, WrappedSpec], RT],
    *args: WrappedSpec.args,
    **kwargs: WrappedSpec.kwargs
) -> Callable[[Future[T]], RT]:
    def callback(completed_future: Future[T]):
        result = completed_future.result()

        return wrapped(result, *args, **kwargs)

    return callback


def pixmap_size_bytes(pixmap: QPixmap) -> int:
    return int((pixmap.height() * pixmap.width() * pixmap.depth()) / 8)


# FIXME: Save the dimentions along with the image path, both have to be the keys, atleast an approximate value
class PixmapCache:
    def __init__(self) -> None:
        super().__init__()

        self._qt_cache = QPixmapCache()
        self._qt_cache.setCacheLimit(DEFAULT_CACHE_LIMIT)
        self._size = 0

        self._load_pool = ThreadPoolExecutor(MAX_LOAD_WORKERS)
        self._event_loop = asyncio.get_event_loop()

    def _format_key(self, key: Path) -> str:
        return str(key.absolute())

    def get(self, key: Path) -> QPixmap | None:
        entry: QPixmap | None = self._qt_cache.find(self._format_key(key))
        return entry

    def get_or_load(
        self,
        key: Path,
        dimentions: Dimentions
    ) -> PixmapOrFuture:
        cached = self.get(key)
        self.is_cached = False

        if cached is not None:
            self.is_cached = True
            return cached

        pixmap_future = self._event_loop.run_in_executor(
            self._load_pool,
            load_and_resize,
            key,
            dimentions
        )

        def insert(value: QPixmap | None, key: Path):
            if value is None:
                return

            self.insert(key, value)


        pixmap_future.add_done_callback(
            get_generic_callback(insert, key)
        )

        return pixmap_future


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
