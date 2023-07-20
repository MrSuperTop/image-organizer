from asyncio import Future
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication


def loading_cursor(wait_for: Future[Any]) -> None:
    QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    def done_handler(_: Future[Any]) -> None:
        QGuiApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)

    wait_for.add_done_callback(done_handler)
