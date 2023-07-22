from collections.abc import Iterable
from pathlib import Path

from PyQt6.QtWidgets import QHBoxLayout, QLayout

from image_organizer.pixmap_cache import PixmapCache
from image_organizer.widgets.folders_list import FoldersList, ForbiddenFoldersFilter
from image_organizer.widgets.viewer.action_buttons import ActionButtons
from image_organizer.widgets.viewer.tags_list import TagsList
from ui.folder_viewer import FolderViewer
from ui.my_splitter import MySplitter


class Viewer(FolderViewer):
    def __init__(
        self,
        image_paths: Iterable[Path],
        to_move: Path | list[Path],
        move_to: Path,
        cache: PixmapCache
    ) -> None:
        self.forbidden_folders = None
        if isinstance(to_move, Path) and to_move.is_dir():
            self.forbidden_folders: ForbiddenFoldersFilter = [(
                to_move,
                'you can\'t select the folder you have chosen as the source folder for your images'
            )]

        self._move_to = move_to
        self._to_move = to_move

        super().__init__(image_paths, cache)

    def gui(self) -> QLayout:
        layout = QHBoxLayout()

        self.splitter = MySplitter()

        self.folders_list = FoldersList(
            self._move_to,
            self.forbidden_folders
        )

        self.folders_list.move_to_changed.connect(self.move_to_changed_handler)

        self.splitter.addWidget(self.folders_list)

        folder_viewer_layout = super().gui()

        self.action_buttons = ActionButtons(
            self
        )

        folder_viewer_layout.addWidget(self.action_buttons)

        self.splitter.addLayout(folder_viewer_layout)

        self.tags_list = TagsList(self)
        self.splitter.addWrappedWidget(self.tags_list)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 4)
        self.splitter.setStretchFactor(2, 1)

        layout.addWidget(self.splitter)
        return layout

    @property
    def move_to(self):
        return self._move_to

    @move_to.setter
    def move_to(self, new_move_to: Path) -> None:
        self._move_to = new_move_to

    def move_to_changed_handler(self, new_move_to: Path) -> None:
        self.move_to = new_move_to
