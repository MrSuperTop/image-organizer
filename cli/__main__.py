import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from pathlib import Path

from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication

from cli.actions.accessible_directory import AccessibleDirectory
from cli.actions.directory_or_glob import DirectoryOrGlob
from cli.MyNamespace import MyNamespace
from image_organizer import MainWindow


def parse_args() -> MyNamespace:
    ap = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter
    )

    ap.add_argument(
        'to_move',
        help='The directory or a glob which specifies which files you would like to move',
        type=Path,
        action=DirectoryOrGlob
    )

    ap.add_argument(
        'move_to',
        help='A directory to which the files will be moved',
        type=Path,
        action=AccessibleDirectory
    )

    nsp = MyNamespace()
    ap.parse_args(namespace=nsp)

    return nsp


def main():
    args = parse_args()
    app = QApplication(sys.argv)

    window = MainWindow(
        args.to_move,
        args.move_to
    )

    window.resize(QSize(1280, 720))

    window.show()
    app.exec()

main()
