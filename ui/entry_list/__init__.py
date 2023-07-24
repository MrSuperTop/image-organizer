from collections.abc import Iterable

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.list_with_menu.list_with_remove import ListWithRemove
from ui.paths_list import LIST_STYLES


class EntryList(QWidget):
    def __init__(
        self,
        possible_entries: Iterable[str],
        default_selected_entries: Iterable[str] = list(),
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.present_entries = set(possible_entries)

        self._layout = self.gui()
        self.setLayout(self._layout)

        for index, entry in enumerate(possible_entries):
            self.add_list_item(entry)

            if entry in default_selected_entries:
                self.list.setCurrentRow(index)

    def gui(self) -> QVBoxLayout | QHBoxLayout:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)


        self.entry_field = QLineEdit()
        self.entry_field.returnPressed.connect(self._add_handler)

        self.list = ListWithRemove[QListWidgetItem]()

        layout.addWidget(self.entry_field)
        layout.addWidget(self.list)

        self.setStyleSheet(LIST_STYLES)

        return layout

    def add_list_item(self, entry: str) -> None:
        self.list.addItem(entry)

    def _add_handler(self) -> None:
        text = self.entry_field.text()
        if text in self.present_entries:
            return

        self.list.addItem(text)
        self.present_entries.add(text)

        self.entry_field.clear()
