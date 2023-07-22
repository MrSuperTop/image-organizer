from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class MovementButtons(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.gui()

    def gui(self) -> None:
        self._layout = QHBoxLayout()
        self._layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.prev_button = QPushButton('Previous')
        self.prev_button.setMaximumWidth(150)
        self.prev_signal = self.prev_button.clicked

        self.next_button = QPushButton('Next')
        self.next_button.setMaximumWidth(150)
        self.next_signal = self.next_button.clicked

        self._layout.addWidget(self.prev_button)
        self._layout.addWidget(self.next_button)

        self.setLayout(self._layout)
