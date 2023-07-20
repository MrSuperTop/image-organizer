import asyncio
from asyncio import AbstractEventLoop, CancelledError, Future
from functools import partial
from pathlib import Path
from typing import Any, Self

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from image_organizer.db import session
from image_organizer.image_utils.find_images import find_images
from image_organizer.pixmap_cache import PixmapCache
from image_organizer.widgets.folders_list import FoldersList, ForbiddenFoldersFilter
from image_organizer.widgets.gallery import Gallery
from image_organizer.widgets.taggable_folder_viewer import TaggableFolderViewer
from ui.my_splitter import MySplitter

# TODO: Implement shortcuts for movement, ctrl + z, etc.
# TODO: Menu actions for opening a new folder or glob
# TODO: i18n
# TODO: Refactor to use snake_case https://www.qt.io/blog/qt-for-python-6-released
# TODO: ABC for widgets how I like it
# TODO: Option to move tagged files into individual folder
# TODO: Option to copy a file instead of moving it
# TODO: Option for recusrsively going through the file tree


class MainWindow(QMainWindow):
    def __init__(
        self,
        # TODO: Get this argument type sorted out or get rid of it all together by loading cwd and adding an option to open a folder
        to_move: Path | list[Path],
        move_to: Path,
        size: QSize
    ) -> None:
        super().__init__()

        self.initial_size = size
        self.resize(size)

        self.to_move = to_move
        self.move_to = move_to
        self.cache = PixmapCache()

        if isinstance(to_move, Path):
            self.images_paths = find_images(to_move)
        else:
            self.images_paths = to_move

        self.gui()

    def gui(self) -> None:
        self.setWindowTitle('Image Organizer')

        self._layout = QHBoxLayout()
        self.splitter = MySplitter(Qt.Orientation.Horizontal)

        forbidden_folders = None
        if isinstance(self.to_move, Path) and self.to_move.is_dir():
            forbidden_folders: ForbiddenFoldersFilter = [(
                self.to_move,
                'you can\'t select the folder you have chosen as the source folder for your images'
            )]

        self.folders_list = FoldersList(
            self.move_to,
            forbidden_folders
        )

        self.folders_list.selected_path.connect(self.move_to_change_handler)

        self.tabs = QTabWidget()
        self.folder_viewer = TaggableFolderViewer(
            self.images_paths,
            self.move_to,
            self.cache
        )

        self.tabs.addTab(self.folder_viewer, 'Viewer')

        self.gallery = Gallery(self.cache, self.folder_viewer.tags_list)
        self.tabs.addTab(self.gallery, 'Gallery')

        self.splitter.addWidget(self.folders_list)

        tabs_wrapper_layout = QVBoxLayout()
        tabs_wrapper_layout.addWidget(self.tabs)

        tabs_wrapper = QWidget()
        tabs_wrapper.setLayout(tabs_wrapper_layout)

        self.splitter.addWidget(tabs_wrapper)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)

        self._layout.addWidget(self.splitter)

        central_widget = QWidget()
        central_widget.setLayout(self._layout)

        self.setCentralWidget(central_widget)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        *_: Any,
    ) -> None:
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

    def move_to_change_handler(self, new_move_to: Path) -> None:
        self.move_to = new_move_to
