from pathlib import Path
from shutil import move

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QPushButton, QVBoxLayout, QWidget
from send2trash import send2trash

from image_organizer.image_utils.find_images import find_images
from image_organizer.widgets.gallery_viewer import GalleryViewer

# TODO: Implement shortcuts
# TODO: Reverse the move with ctrl+Z, move to trash confirmation


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
        self.setWindowTitle('File mover')

        self._layout = QVBoxLayout()
        self.viewer = GalleryViewer(self.image_paths, (1280, 720))

        self._layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self.viewer)

        self.setup_buttons()
        self._layout.addLayout(self.buttons_layout)

        widget = QWidget()
        widget.setLayout(self._layout)

        self.setCentralWidget(widget)


    def next_handler(self) -> None:
        self.viewer.next()

    def prev_handler(self) -> None:
        self.viewer.prev()

    def move_handler(self) -> None:
        move(self.viewer.current_image_path, self.move_to)
        self.viewer.clear_and_switch()

    def trash_handler(self) -> None:
        send2trash(self.viewer.current_image_path)
        self.viewer.clear_and_switch()
