import asyncio
import functools
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


# TODO: Move the async logic somewhere else
async def main(app: QApplication):
    create_schema()

    def close_future(
        window: MainWindow,
        future: asyncio.Future[None],
        loop: asyncio.AbstractEventLoop
    ) -> None:
        window.clean_up()

        loop.call_later(10, future.cancel)
        future.cancel()

    loop = asyncio.get_event_loop()
    future: asyncio.Future[None]= asyncio.Future()

    args = parse_args()

    window = MainWindow(
        args.to_move,
        args.move_to,
        QSize(1280, 720)
    )

    app.aboutToQuit.connect(
        functools.partial(close_future, window, future, loop)
    )

    window.show()

    try:
        await future
    except asyncio.CancelledError:
        return True


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
