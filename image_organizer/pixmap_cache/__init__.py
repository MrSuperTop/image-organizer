from __future__ import annotations

import asyncio
from asyncio import Future
from collections.abc import Callable
from concurrent.futures import Executor, ThreadPoolExecutor
from functools import wraps
from pathlib import Path
from typing import Concatenate, ParamSpec, TypeVar, overload

from PyQt6.QtGui import QPixmap

from image_organizer.image_utils.load_and_resize import Dimentions, load_and_resize
from image_organizer.pixmap_cache.cache_entry import CacheEntry
from image_organizer.utils.into_callback import into_callback

DEFAULT_CACHE_LIMIT = 1024 * 1024 # 1GB
MAX_LOAD_WORKERS = 128


CacheEntryOrFuture = CacheEntry | Future[CacheEntry | None]
PixmapOrFuture = QPixmap | Future[QPixmap | None]

Key = Path
DecoratedSpec = ParamSpec('DecoratedSpec')
RT = TypeVar('RT')


def _format_key(
    func: Callable[Concatenate[PixmapCache, Key, DecoratedSpec], RT]
) -> Callable[Concatenate[PixmapCache, Key, DecoratedSpec], RT]:
    @wraps(func)
    def inner(
        self: PixmapCache,
        key: Key,
        *args: DecoratedSpec.args,
        **kwargs: DecoratedSpec.kwargs
    ) -> RT:
        formatted_key = key.absolute()
        return func(self, formatted_key, *args, **kwargs)
    return inner


class PixmapCache:
    def __init__(
        self,
        cache_limit_kbytes: int = DEFAULT_CACHE_LIMIT,
        custom_load_executor: Executor | None = None
    ) -> None:
        super().__init__()

        # TODO: Inforce the cache limit, delete the oldset record or the least used one
        self._cache_limit = cache_limit_kbytes
        self._cache: dict[Key, list[CacheEntry]] = dict()
        self._size = 0

        self._event_loop = asyncio.get_running_loop()
        if custom_load_executor is None:
            self._load_executor = ThreadPoolExecutor(MAX_LOAD_WORKERS)
        else:
            self._load_executor = custom_load_executor

    @overload
    def get(self, key: Key) -> list[CacheEntry] | None: ...
    @overload
    def get(self, key: Key, dimentions: Dimentions) -> CacheEntry | None: ...

    @_format_key
    def get(
        self,
        key: Key,
        dimentions: Dimentions | None = None
    ) -> list[CacheEntry] | CacheEntry | None:
        if key not in self._cache:
            return

        entries = self._cache.get(key, None)
        if dimentions is None or entries is None:
            return entries

        find_generator = (entry for entry in entries if entry.dimentions == dimentions)
        return next(find_generator, None)

    @_format_key
    def insert(self, key: Key, entry: CacheEntry) -> None:
        self._size += entry.pixmap_size_bytes()

        if key in self._cache:
            self._cache[key].append(entry)
            return

        self._cache[key] = [entry]

    def _load_image(
        self,
        image_path: Path,
        dimentions: Dimentions
    ) -> tuple[Future[QPixmap | None], Future[CacheEntry | None]]:
        entry_future: Future[CacheEntry | None] = self._event_loop.create_future()
        pixmap_future = self._event_loop.run_in_executor(
            self._load_executor,
            load_and_resize,
            image_path,
            dimentions
        )

        def insert_handler(value: QPixmap | None, image_path: Path):
            if entry_future.done():
                return

            if value is None:
                entry_future.set_result(value)
                return

            new_entry = CacheEntry(
                value,
                dimentions
            )

            self.insert(image_path, new_entry)
            entry_future.set_result(new_entry)


        pixmap_future.add_done_callback(
            into_callback(insert_handler, image_path)
        )

        return pixmap_future, entry_future

    def get_or_load(
        self,
        image_path: Path,
        dimentions: Dimentions
    ) -> CacheEntryOrFuture:
        cached = self.get(image_path, dimentions)

        if cached is not None:
            return cached

        _, entry_future = self._load_image(image_path, dimentions)
        return entry_future

    def get_or_load_pixmap(
        self,
        image_path: Path,
        dimentions: Dimentions
    ) -> PixmapOrFuture:
        cached = self.get(image_path, dimentions)

        if cached is not None:
            return cached.pixmap

        pixmap_future, _ = self._load_image(image_path, dimentions)
        return pixmap_future

    @overload
    def delete(self, key: Key) -> bool: ...
    @overload
    def delete(self, key: Key, dimentions: Dimentions) -> bool: ...

    @_format_key
    def delete(self, key: Key, dimentions: Dimentions | None = None) -> bool:
        if key not in self._cache:
            return False

        to_delete = self._cache[key]
        if dimentions is None:
            for entry in to_delete:
                self._size -= entry.pixmap_size_bytes()

            del self._cache[key]
            return True

        entry_find = (
            (index, entry) for index, entry in enumerate(to_delete)
            if entry.dimentions == dimentions
        )

        found = next(entry_find, None)
        if found is None:
            return False

        index, entry = found

        self._size -= entry.pixmap_size_bytes()
        del to_delete[index]
        return True

    @property
    def size_kbytes(self) -> float:
        return self._size / 1024

    @property
    def size_mb(self) -> float:
        return self._size / 1024 ** 2
