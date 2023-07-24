from __future__ import annotations

import shutil
import typing
from pathlib import Path

from PyQt6.QtWidgets import QMessageBox, QPushButton, QVBoxLayout, QWidget
from send2trash import send2trash as send_to_trash

from image_organizer.db import session
from image_organizer.db.models.image import Image
from image_organizer.widgets.viewer.action_buttons.new_filename_dialog import (
    NewFilenameDialog,
)
from ui.folder_viewer import ImageChangedData

if typing.TYPE_CHECKING:
    from image_organizer.widgets.viewer import Viewer


class ActionButtons(QWidget):
    def __init__(
        self,
        connected_viewer: Viewer,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)


        self._move_to: Path | None = None
        self._image_path: Path
        self._image: Image

        self._viewer = connected_viewer
        connected_viewer.folders_list.move_to_changed.connect(self._move_to_changed_handler)
        connected_viewer.image_changed.connect(self._image_changed_handler)

        self.gui()

    def gui(self) -> None:
        self.trash_confirmation = QMessageBox()
        self.trash_confirmation.setIcon(QMessageBox.Icon.Warning)
        self.trash_confirmation.setStandardButtons(
            QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
        )

        self._layout = QVBoxLayout()

        self.move_button = QPushButton('Move to folder')
        self.move_button.clicked.connect(self._move_handler)

        trash_button = QPushButton('Move to trash')
        trash_button.clicked.connect(self._trash_handler)

        self._layout.addWidget(self.move_button)
        self._layout.addWidget(trash_button)

        self.setLayout(self._layout)

    def _move_to_changed_handler(self, new_move_to: Path | None) -> None:
        self.move_button.setDisabled(new_move_to is None)
        self._move_to = new_move_to

    def _image_changed_handler(self, signal_data: ImageChangedData) -> None:
        self._image_path = signal_data.image.format_path()
        self._image = signal_data.image

    def _move_handler(self) -> None:
        if self._move_to is None:
            return

        destination_path = self._move_to.joinpath(self._image_path.name)
        if destination_path.exists():
            new_filename_dialog = NewFilenameDialog(
                destination_path,
                self._image_path,
                self
            )

            is_accepted = bool(new_filename_dialog.exec())

            if not is_accepted or new_filename_dialog.new_filepath is None:
                return

            destination_path = new_filename_dialog.new_filepath

        shutil.move(self._image_path, destination_path)

        self._image.path = Image.path_formatter(destination_path)
        session.commit()

        self._viewer.clear_and_switch()

    def _trash_handler(self) -> None:
        to_trash = self._image_path
        self.trash_confirmation.setText(
            f'Are you sure you want to move {to_trash} to trash?'
        )

        selected = self.trash_confirmation.exec()
        if selected != QMessageBox.StandardButton.Yes:
            return

        send_to_trash(to_trash)
        session.delete(self._image)
        session.commit()

        self._viewer.clear_and_switch()
