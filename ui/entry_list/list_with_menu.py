from dataclasses import dataclass
from typing import cast

from PyQt6 import QtGui
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QMenu, QWidget


@dataclass
class ContextMenuSelectedData:
    action: QAction
    affected_item: QListWidgetItem


class ListWithMenu(QListWidget):
    context_menu_selected = pyqtSignal(object)

    def __init__(
        self,
        context_menu_actions: list[QAction],
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.gui(context_menu_actions)

    def gui(self, actions: list[QAction]) -> None:
        self._context_menu = QMenu()

        for action in actions:
            self._context_menu.addAction(action)

    def contextMenuEvent(self, a0: QtGui.QContextMenuEvent) -> None:
        super().contextMenuEvent(a0)

        # * Casting, as there can be no item on the event position
        affected_item = cast(
            QListWidgetItem | None,
            self.itemAt(a0.pos())
        )

        if affected_item is None:
            return

        # * Casting, as the list contex menu can be simply closed without selecting 
        action = cast(
            QAction | None,
            self._context_menu.exec(a0.globalPos())
        )

        if action is None:
            return

        signal_data = ContextMenuSelectedData(
            action,
            affected_item
        )

        self.context_menu_selected.emit(signal_data)
