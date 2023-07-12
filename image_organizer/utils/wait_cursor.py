from contextlib import contextmanager

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication


@contextmanager
def wait_cursor():
    QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

    try:
        yield
    finally:
        QGuiApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
