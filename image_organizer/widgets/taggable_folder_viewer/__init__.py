from collections.abc import Iterable
from pathlib import Path

from image_organizer.pixmap_cache import PixmapCache
from image_organizer.widgets.taggable_folder_viewer.control_buttons_group import (
    ControlButtonsGroup,
)
from image_organizer.widgets.taggable_folder_viewer.tags_list import TagsList
from ui.folder_viewer import FolderViewer


class TaggableFolderViewer(FolderViewer):
    def __init__(
        self,
        image_paths: Iterable[Path],
        move_to: Path,
        cache: PixmapCache
    ) -> None:
        super().__init__(
            image_paths,
            cache
        )

        self._move_to = move_to

    def gui(self) -> None:
        super().gui()

        self.control_buttons = ControlButtonsGroup(
            self
        )

        self._layout.addWidget(self.control_buttons)

    @property
    def tags_list(self) -> TagsList:
        return self.control_buttons.tags_list

    @property
    def move_to(self):
        return self._move_to

    @move_to.setter
    def move_to(self, new_move_to: Path) -> None:
        self._move_to = new_move_to
