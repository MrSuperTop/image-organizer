import asyncio
import os
from asyncio import AbstractEventLoop, CancelledError, Future
from functools import partial
from pathlib import Path
from typing import Any, Self

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QGuiApplication
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QMenuBar, QTabWidget, QWidget

from image_organizer.db import session
from image_organizer.errors import (
    IsNotADirectoryError,
    NoImagesFoundError,
    SamePathError,
)
from image_organizer.image_utils.find_images import find_images
from image_organizer.main_window.dialogs.distribute_dialog import DistributeDialog
from image_organizer.pixmap_cache import PixmapCache
from image_organizer.widgets.gallery import Gallery
from image_organizer.widgets.viewer import Viewer
from ui.my_splitter import MySplitter

# TODO: Implement shortcuts for movement, ctrl + z, etc.
# TODO: Menu actions for opening a new folder or glob
# TODO: i18n
# TODO: Refactor to use snake_case https://www.qt.io/blog/qt-for-python-6-released
# TODO: ABC for widgets and the main window how I like it
# TODO: Option to move tagged files into individual folder
# TODO: Option to copy a file instead of moving it
# TODO: Option for recusrsively going through the file tree


class MainWindow(QMainWindow):
    def __init__(
        self,
        to_move: Path | list[Path],
        move_to: list[Path],
        size: QSize
    ) -> None:
        super().__init__()

        self.initial_size = size
        self.resize(size)

        self.to_move = to_move
        self.move_to = move_to
        self.cache = PixmapCache()

        if isinstance(to_move, Path):
            to_move = to_move.absolute()

            for single_dir in map(Path.absolute, move_to):
                if not single_dir.is_dir():
                    raise IsNotADirectoryError(single_dir)

                if to_move == single_dir:
                    raise SamePathError(to_move, single_dir)

            self.images_paths = find_images(to_move)
        else:
            self.images_paths = to_move

        if len(self.images_paths) == 0:
            raise NoImagesFoundError(to_move)

        self.gui()

    def _create_menu_bar(self) -> QMenuBar:
        menu_bar = QMenuBar()
        export_menu = menu_bar.addMenu('Distribute')

        self.distribute_action = QAction('Distribute by tags', self)

        self.distribute_action.triggered.connect(self._distribute_by_tags_handler)
        export_menu.addAction(self.distribute_action)

        return menu_bar

    def gui(self) -> None:
        self.setWindowTitle('Image Organizer')

        self._menu_bar = self._create_menu_bar()
        self.setMenuBar(self._menu_bar)

        self._layout = QHBoxLayout()
        self.splitter = MySplitter(Qt.Orientation.Horizontal)

        self.tabs = QTabWidget()
        self.viewer = Viewer(
            self.images_paths,
            self.to_move,
            self.move_to,
            self.cache
        )

        self.tabs.addTab(self.viewer, 'Viewer')

        self.gallery = Gallery(self.cache, self.viewer.tags_list)
        self.tabs.addTab(self.gallery, 'Gallery')

        self._layout.addWidget(self.tabs)

        central_widget = QWidget()
        central_widget.setLayout(self._layout)

        self.setCentralWidget(central_widget)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        *_: Any,
    ) -> None:
        session.commit()
        session.close_all()

    async def show_async(
        self,
        app: QGuiApplication,
        event_loop: AbstractEventLoop
    ) -> None:
        future = event_loop.create_future()
        def quit_handler(to_cancel: Future[Any]) -> None:
            to_cancel.cancel()

        app.aboutToQuit.connect(partial(quit_handler, future))

        self.show()

        try:
            await asyncio.ensure_future(future, loop=event_loop)
        except CancelledError:
            return

    def _distribute_by_tags_handler(self) -> None:
        session.commit()

        # TODO: Select which images will be distributed, of instance, only the images which are in the currenly "opened" folder
        if isinstance(self.to_move, Path):
            distribute_from = self.to_move
        else:
            distribute_from = next(iter(self.to_move), Path(os.getcwd()).parents[-1])

        distribute_dialog = DistributeDialog(self.cache, distribute_from, self)
        distribute_dialog.exec()