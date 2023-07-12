from collections.abc import Iterable

from PyQt6.QtWidgets import QLineEdit, QListWidget, QVBoxLayout, QWidget

from ui.paths_list import LIST_STYLES


class EntryList(QWidget):
    def __init__(
        self,
        possible_entries: Iterable[str],
        default_selected_entries: Iterable[str] = list(),
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.possible_entries = list(possible_entries)
        self.selected_entries = list(default_selected_entries)

        self.gui()

        for index, entry in enumerate(possible_entries):
            self.add_list_item(entry)

            if entry in default_selected_entries:
                self.list.setCurrentRow(index)

    def add_list_item(self, entry: str) -> None:
        self.list.addItem(entry)

    def gui(self, *before_widgets: QWidget) -> None:
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)

        self.list = QListWidget()

        self.entry_field = QLineEdit()
        self.entry_field.returnPressed.connect(self._add_handler)

        for widget in before_widgets:
            self._layout.addWidget(widget)

        self._layout.addWidget(self.list)
        self._layout.addWidget(self.entry_field)

        self.setLayout(self._layout)
        self.setStyleSheet(LIST_STYLES)

    def _add_handler(self) -> None:
        text = self.entry_field.text()
        self.list.addItem(text)

        self.entry_field.clear()
