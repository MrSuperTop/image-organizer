from __future__ import annotations

import typing
from shutil import move

from PyQt6.QtWidgets import QMessageBox, QPushButton, QVBoxLayout, QWidget
from send2trash import send2trash

if typing.TYPE_CHECKING:

    from image_organizer.widgets.taggable_folder_viewer import TaggableFolderViewer


class ActionButtonsGroup(QWidget):
    def __init__(
        self,
        connected_gallery: TaggableFolderViewer,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.gallery = connected_gallery

        self.gui()

    def gui(self) -> None:
        self.trash_confirmation = QMessageBox()
        self.trash_confirmation.setIcon(QMessageBox.Icon.Warning)
        self.trash_confirmation.setStandardButtons( QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
        )

        self._layout = QVBoxLayout()

        move_button = QPushButton('Move to folder')
        move_button.clicked.connect(self.move_handler)

        trash_button = QPushButton('Move to trash')
        trash_button.clicked.connect(self.trash_handler)

        self._layout.addWidget(move_button)
        self._layout.addWidget(trash_button)

        self.setLayout(self._layout)

    def next_handler(self) -> None:
        self.gallery.next()

    def prev_handler(self) -> None:
        self.gallery.prev()

    # FIXME: Update the image path in the db
    def move_handler(self) -> None:
        move(self.gallery.current_image_path, self.gallery.move_to)
        self.gallery.clear_and_switch()

    def trash_handler(self) -> None:
        to_trash = self.gallery.current_image_path

        self.trash_confirmation.setText(
            f'Are you sure you want to move {to_trash} to trash?'
        )

        selected = self.trash_confirmation.exec()
        if selected != QMessageBox.StandardButton.Yes:
            return

        send2trash(to_trash)
        self.gallery.clear_and_switch()
