import asyncio
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from pathlib import Path

import qasync
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication

from cli.actions.accessible_directory import AccessibleDirectory
from cli.actions.directory_or_glob import DirectoryOrGlob
from cli.MyNamespace import MyNamespace
from image_organizer import MainWindow
from image_organizer.db import create_schema


def parse_args() -> MyNamespace:
    ap = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter
    )

    ap.add_argument(
        'to_move',
        help='The directory from which you want to move file or a glob which specifies which files you would like to move',
        type=Path,
        action=DirectoryOrGlob
    )

    # TODO: Make this optional and block the button
    ap.add_argument(
        'move_to',
        help='The default directory to which the files will be moved',
        type=Path,
        action=AccessibleDirectory
    )

    nsp = MyNamespace()
    ap.parse_args(namespace=nsp)

    return nsp


async def main(app: QApplication):
    create_schema()

    loop = asyncio.get_event_loop()
    args = parse_args()

    with MainWindow(
        args.to_move,
        args.move_to,
        QSize(1280, 720)
    ) as window:
        await window.show_async(app, loop)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    if sys.version_info.major == 3 and sys.version_info.minor == 11:
        with qasync._set_event_loop_policy( # type: ignore
            qasync.DefaultQEventLoopPolicy()
        ):
            runner = asyncio.runners.Runner()
            try:
                runner.run(main(app))
            finally:
                runner.close()
    else:
        qasync.run(main(app)) # type: ignore
