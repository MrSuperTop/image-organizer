import os
import os.path
from pathlib import Path
from typing import cast

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QAbstractItemView, QListWidget, QListWidgetItem, QWidget
from showinfm import show_in_file_manager

from ui.list_with_menu import ContextMenuSelectedData
from ui.list_with_menu.list_with_remove import ListWithRemove
from ui.path_utils.absolute_paths import absolute_paths

LIST_STYLES = """
QListWidget::item:selected {
    background-color: #219ebc;
    color: #ffffff;
}
"""



@absolute_paths
def get_path_label(
    into_label: Path,
    relative_to: Path | None = None
) -> str:
    if relative_to is None:
        relative_to = Path(os.getcwd())

    common_relative = Path(os.path.commonpath((into_label, relative_to)))
    common_is_root = common_relative.anchor == str(common_relative)

    relative_to_common = into_label.relative_to(common_relative)

    result = str(relative_to_common)
    if common_is_root:
        result = f'{common_relative.anchor}{result}'
    elif common_relative.absolute() == Path(os.getcwd()):
        result = f'.{os.path.sep}{result}'

    return result


class PathListItem(QListWidgetItem):
    def __init__(
        self,
        path: Path,
        working_dir: Path = Path(os.getcwd()),
        parent: QListWidget | None = None,
        type: QListWidgetItem.ItemType = QListWidgetItem.ItemType.Type,
    ) -> None:
        label = get_path_label(path, working_dir)
        self.path = path

        super().__init__(label, parent, type)


class PathsList(ListWithRemove[PathListItem]):
    def __init__(
        self,
        *,
        mininum_lenght: int = 0,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self._open_in_explorer_action = QAction('Open folder in explorer')
        self.add_action(self._open_in_explorer_action, self._open_in_explorer_handler)

        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.minimum_length = mininum_lenght

        self.setStyleSheet(LIST_STYLES)

    def add_path(self, path: Path) -> PathListItem:
        new_item = PathListItem(path)
        self.addItem(new_item)

        return new_item

    @property
    def selected(self) -> PathListItem | None:
        all_selected = self.selectedItems()
        if len(all_selected) == 0:
            return

        # * Casting, as a custom QListWidgetItem is being used
        return cast(
            PathListItem,
            all_selected[0]
        )

    def _open_in_explorer_handler(
        self,
        signal_data: ContextMenuSelectedData[PathListItem]
    ) -> None:
        path = signal_data.affected_item.path.absolute()
        show_in_file_manager(str(path))
