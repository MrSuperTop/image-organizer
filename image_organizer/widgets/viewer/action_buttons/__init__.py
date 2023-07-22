from __future__ import annotations

import shutil
import typing

from PyQt6.QtWidgets import QMessageBox, QPushButton, QVBoxLayout, QWidget
from send2trash import send2trash as send_to_trash

from image_organizer.db import session
from image_organizer.db.models.image import Image
from image_organizer.widgets.viewer.action_buttons.new_filename_dialog import (
    NewFilenameDialog,
)

if typing.TYPE_CHECKING:
    from image_organizer.widgets.viewer import Viewer


class ActionButtons(QWidget):
    def __init__(
        self,
        connected_viewer: Viewer,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.viewer = connected_viewer

        self.gui()

    def gui(self) -> None:
        self.trash_confirmation = QMessageBox()
        self.trash_confirmation.setIcon(QMessageBox.Icon.Warning)
        self.trash_confirmation.setStandardButtons(
            QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
        )

        self._layout = QVBoxLayout()

        move_button = QPushButton('Move to folder')
        move_button.clicked.connect(self.move_handler)

        trash_button = QPushButton('Move to trash')
        trash_button.clicked.connect(self.trash_handler)

        self._layout.addWidget(move_button)
        self._layout.addWidget(trash_button)

        self.setLayout(self._layout)

    def move_handler(self) -> None:
        destination_path = self.viewer.move_to.joinpath(self.viewer.current_image_path.name)
        if destination_path.exists():
            new_filename_dialog = NewFilenameDialog(
                destination_path,
                self.viewer.current_image_path,
                self
            )

            is_accepted = bool(new_filename_dialog.exec())

            if not is_accepted or new_filename_dialog.new_filepath is None:
                return

            destination_path = new_filename_dialog.new_filepath

        self.viewer
        shutil.move(self.viewer.current_image_path, destination_path)

        self.viewer.current_image.path = Image.path_formatter(destination_path)
        session.commit()

        self.viewer.clear_and_switch()

    def trash_handler(self) -> None:
        to_trash = self.viewer.current_image_path

        self.trash_confirmation.setText(
            f'Are you sure you want to move {to_trash} to trash?'
        )

        selected = self.trash_confirmation.exec()
        if selected != QMessageBox.StandardButton.Yes:
            return

        send_to_trash(to_trash)
        session.delete(self.viewer.current_image)
        session.commit()

        self.viewer.clear_and_switch()
