from __future__ import annotations

import typing
from shutil import move

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QMessageBox, QPushButton, QVBoxLayout, QWidget
from send2trash import send2trash

from image_organizer.widgets.taggable_folder_viewer.tags_list import TagsList

if typing.TYPE_CHECKING:

    from image_organizer.widgets.taggable_folder_viewer import TaggableFolderViewer


class ControlButtonsGroup(QWidget):
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
        self.trash_confirmation.setStandardButtons(
            QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
        )

        self._layout = QVBoxLayout()

        actions_layout = QHBoxLayout()

        self.tags_list = TagsList(
            self.gallery
        )
        actions_layout.addWidget(self.tags_list, 80)

        action_buttons_layout = QVBoxLayout()
        action_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        move_button = QPushButton('Move to folder')
        move_button.clicked.connect(self.move_handler)

        trash_button = QPushButton('Move to trash')
        trash_button.clicked.connect(self.trash_handler)

        action_buttons_layout.addWidget(move_button)
        action_buttons_layout.addWidget(trash_button)

        actions_layout.addLayout(action_buttons_layout, 20)

        # TODO: find a better place for the galery control buttons, maybe under the
        # image viewer. When the texts will be incapsulated, there will be more room
        # for the image switching logic

        movement_buttons_layout = QHBoxLayout()
        movement_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        prev_button = QPushButton('Previous')
        prev_button.clicked.connect(self.prev_handler)
        prev_button.setMaximumWidth(150)

        next_button = QPushButton('Next')
        next_button.clicked.connect(self.next_handler)
        next_button.setMaximumWidth(150)

        movement_buttons_layout.addWidget(prev_button)
        movement_buttons_layout.addWidget(next_button)

        self._layout.addLayout(movement_buttons_layout)
        self._layout.addLayout(actions_layout)

        self.setLayout(self._layout)

    def next_handler(self) -> None:
        self.gallery.next()

    def prev_handler(self) -> None:
        self.gallery.prev()

    def move_handler(self) -> None:
        move(self.gallery.current_image_path, self.gallery.move_to)
        self.gallery.clear_and_switch()

    # TODO: Update the image path in the db
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
