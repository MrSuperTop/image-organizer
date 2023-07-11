from pathlib import Path
from shutil import move

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from send2trash import send2trash

from image_organizer.image_utils.find_images import find_images
from image_organizer.widgets.folders_list import FoldersList, ForbiddenFoldersFilter
from image_organizer.widgets.gallery_viewer import GalleryViewer
from image_organizer.widgets.my_splitter import MySplitter

# TODO: Implement shortcuts
# TODO: i18n
# TODO: Reverse the move with ctrl+Z, move to trash confirmation
# TODO: Refactor to use snake_case https://www.qt.io/blog/qt-for-python-6-released


class MainWindow(QMainWindow):
    def __init__(
        self,
        to_move: Path | list[Path],
        move_to: Path
    ):
        super().__init__()

        self.to_move = to_move
        self.move_to = move_to

        if isinstance(to_move, Path):
            image_paths = find_images(to_move)
        else:
            image_paths = to_move

        self.image_paths = image_paths

        self.gui()

    def setup_buttons(self) -> None:
        self.buttons_layout = QVBoxLayout()

        self.trash_confirmation = QMessageBox()
        self.trash_confirmation.setIcon(QMessageBox.Icon.Warning)
        self.trash_confirmation.setStandardButtons(
            QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
        )

        move_button = QPushButton('Move to folder')
        move_button.clicked.connect(self.move_handler)

        trash_button = QPushButton('Move to trash')
        trash_button.clicked.connect(self.trash_handler)

        movement_buttons_layout = QHBoxLayout()
        prev_button = QPushButton('Previous')
        prev_button.clicked.connect(self.prev_handler)

        next_button = QPushButton('Next')
        next_button.clicked.connect(self.next_handler)

        movement_buttons_layout.addWidget(prev_button)
        movement_buttons_layout.addWidget(next_button)

        self.buttons_layout.addWidget(move_button)
        self.buttons_layout.addWidget(trash_button)
        self.buttons_layout.addLayout(movement_buttons_layout)

    def gui(self) -> None:
        self.setWindowTitle('Image Organizer')

        self._layout = QHBoxLayout()
        self.splitter = MySplitter(Qt.Orientation.Horizontal)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(2, 2)

        forbidden_folders = None
        if isinstance(self.to_move, Path) and self.to_move.is_dir():
            forbidden_folders: ForbiddenFoldersFilter = [(
                self.to_move,
                'you can\'t select the folder you have chosen as the source folder for your images'
            )]

        self.folders_list = FoldersList(
            self.move_to,
            forbidden_folders
        )

        self.folders_list.selected_path.connect(self.move_to_change_handler)

        self.splitter.addWidget(self.folders_list)

        self.main_layout = QVBoxLayout()
        self.viewer = GalleryViewer(self.image_paths, (1280, 720))

        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.viewer)

        self.setup_buttons()
        self.main_layout.addLayout(self.buttons_layout)

        main_layout_wrapper = QWidget()
        main_layout_wrapper.setLayout(self.main_layout)

        self.splitter.addWidget(main_layout_wrapper)
        self._layout.addWidget(self.splitter)

        widget = QWidget()
        widget.setLayout(self._layout)

        self.setCentralWidget(widget)

    def move_to_change_handler(self, new_move_to: Path) -> None:
        self.move_to = new_move_to

    def next_handler(self) -> None:
        self.viewer.next()

    def prev_handler(self) -> None:
        self.viewer.prev()

    def move_handler(self) -> None:
        move(self.viewer.current_image_path, self.move_to)
        self.viewer.clear_and_switch()

    def trash_handler(self) -> None:
        to_trash = self.viewer.current_image_path

        self.trash_confirmation.setText(
            f'Are you sure you want to move {to_trash} to trash?'
        )

        selected = self.trash_confirmation.exec()
        if selected != QMessageBox.StandardButton.Yes:
            return

        send2trash(to_trash)
        self.viewer.clear_and_switch()
