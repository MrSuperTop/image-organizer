from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QWidget

from ui.list_with_menu import ContextMenuSelectedData, ListItem, ListWithMenu


class ListWithRemove(ListWithMenu[ListItem]):
    def __init__(
        self,
        parent: QWidget | None = None
    ) -> None:
        self.remove_action = QAction('Remove')

        super().__init__(parent)
        self.add_action(self.remove_action, self._remove_handler)

    def _remove_handler(self, signal_data: ContextMenuSelectedData[ListItem]):
        to_remove_index = self.row(signal_data.affected_item)
        self.takeItem(to_remove_index)
