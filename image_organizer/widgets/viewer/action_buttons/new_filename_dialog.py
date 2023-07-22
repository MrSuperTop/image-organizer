from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)


class NewFilenameDialog(QDialog):
    def __init__(
        self,
        file_to_move: Path,
        collision_at: Path,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.file_to_move = file_to_move
        self.colliding_path = collision_at
        self.new_filepath: Path | None = None

        self._layout = self.gui()
        self.setLayout(self._layout)

    def gui(self) -> QVBoxLayout:
        layout = QVBoxLayout()

        input_layout = QVBoxLayout()

        self.info_label = QLabel(f'At file at "{self.colliding_path}" is already present, please provide an alternative filename for "{self.file_to_move.name}"')
        self.already_exists_message = QMessageBox()

        self.input_label = QLabel('New image filename:')
        self.input_field = QLineEdit()

        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_field)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        self.button_box.accepted.connect(self._accept_handler)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.info_label)
        layout.addLayout(input_layout)
        layout.addWidget(self.button_box)

        return layout

    def _accept_handler(self) -> None:
        new_filename = self.input_field.text().strip()
        if len(new_filename) == 0:
            return

        new_path = self.colliding_path.parent / Path(new_filename)
        if self.colliding_path.suffix != new_path.suffix:
            new_name = f'{new_path.name}{self.colliding_path.suffix}'
            new_path = new_path.parent / new_name

        if new_path.exists():
            message_text = f'A file at "{new_path}" also already exists'
            self.already_exists_message.setText(message_text)
            self.already_exists_message.exec()

            return

        self.new_filepath = new_path
        self.accept()
