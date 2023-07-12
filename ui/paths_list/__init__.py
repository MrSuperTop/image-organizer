from pathlib import Path

from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QWidget,
)

# TODO: Better looking paths, shorten them somehow
# TODO: Reveal in the file explorer context menu option

LIST_STYLES = """
QListWidget::item:selected {
    background-color: #219ebc;
    color: #ffffff;
}
"""

class PathListItem(QListWidgetItem):
    def __init__(
        self,
        path: Path,
        parent: QListWidget | None = None,
        type: QListWidgetItem.ItemType = QListWidgetItem.ItemType.Type,
    ) -> None:
        text = str(path.absolute())
        super().__init__(text, parent, type)

        self.setData(Qt.ItemDataRole.UserRole, path)


class PathsList(QListWidget):
    def __init__(
        self,
        *,
        mininum_lenght: int = 0,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.minimum_length = mininum_lenght

        self._context_menu = QMenu()
        self._remove_action = self._context_menu.addAction('Remove')

        self.setStyleSheet(LIST_STYLES)

    def add_path(self, path: Path) -> None:
        new_item = PathListItem(path)
        self.addItem(new_item)

    def contextMenuEvent(self, a0: QtGui.QContextMenuEvent) -> None:
        super().contextMenuEvent(a0)

        effected_item = self.itemAt(a0.pos())
        action = self._context_menu.exec(a0.globalPos())

        if action == self._remove_action and self.count() > self.minimum_length:
            self.takeItem(self.row(effected_item))
