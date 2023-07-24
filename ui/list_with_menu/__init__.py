from __future__ import annotations

import hashlib
from abc import ABC
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar, cast

from PyQt6 import QtGui
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QMenu, QWidget

ListItem = TypeVar('ListItem', bound=QListWidgetItem)

@dataclass
class ContextMenuSelectedData(Generic[ListItem]):
    action: QAction
    affected_item: ListItem


Handler = Callable[[ContextMenuSelectedData[ListItem]], None]
Handlers = list[Handler[ListItem]]


class MenuWithHandlers(Generic[ListItem], QMenu):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._handlers: dict[str, Handlers[ListItem]] = dict()
        self._actions: list[tuple[str, QAction]] = []

    @staticmethod
    def key_from_action(action: QAction) -> str:
        hash = hashlib.md5()
        hash.update(action.text().encode('utf-8'))

        # * May also be None
        assigned_menu = cast(QMenu | None, action.menu())

        if assigned_menu is not None:
            hash.update(bytes(id(assigned_menu)))

        return hash.hexdigest()

    def add_action(self, action: QAction, *handlers: Handler[ListItem]):
        key = self.key_from_action(action)

        self.addAction(action)

        self._actions.append((key, action))
        if key in self._handlers:
            self._handlers[key].extend(handlers)
            return

        self._handlers[key] = list(handlers)

    def get_handlers(self, action: QAction) -> Handlers[ListItem] | None:
        key = self.key_from_action(action)

        if key not in self._handlers:
            return

        return self._handlers[key]

    def actions(self) -> list[QAction]:
        return list(map(lambda item: item[1], self._actions))


class ListWithMenu(Generic[ListItem], QListWidget):
    __metaclass__ = ABC

    context_menu_selected = pyqtSignal(object)

    def __init__(
        self,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.gui()

    def gui(self) -> None:
        self.menu = MenuWithHandlers[ListItem]()
        self.add_action = self.menu.add_action

        self.context_menu_selected.connect(self._context_menu_selected_handler)

    def contextMenuEvent(self, a0: QtGui.QContextMenuEvent) -> None:
        super().contextMenuEvent(a0)

        # * Casting, as there can be no item on the event position
        affected_item = cast(
            ListItem | None,
            self.itemAt(a0.pos())
        )

        if affected_item is None:
            return

        # * Casting, as the list contex menu can be simply closed without selecting
        action = cast(
            QAction | None,
            self.menu.exec(a0.globalPos())
        )

        if action is None:
            return

        signal_data = ContextMenuSelectedData(
            action,
            affected_item
        )

        self.context_menu_selected.emit(signal_data)

    def _context_menu_selected_handler(
        self,
        signal_data: ContextMenuSelectedData[ListItem]
    ) -> None:
        handlers = self.menu.get_handlers(signal_data.action)
        if handlers is None:
            return

        for handler in handlers:
            handler(signal_data)
