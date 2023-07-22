from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QEnterEvent
from PyQt6.QtWidgets import (
    QApplication,
    QLayout,
    QSplitter,
    QSplitterHandle,
    QVBoxLayout,
    QWidget,
)


class MySplitterHandle(QSplitterHandle):
    def enterEvent(self, event: QEnterEvent):
        super().enterEvent(event)

        new_cursor = Qt.CursorShape.SplitHCursor
        if self.orientation() == Qt.Orientation.Vertical:
            new_cursor = Qt.CursorShape.SplitVCursor

        QApplication.setOverrideCursor(new_cursor)

    def leaveEvent(self, a0: QEvent) -> None:
        super().leaveEvent(a0)

        QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)


class MySplitter(QSplitter):
    def createHandle(self) -> QSplitterHandle:
        self.split_handle = MySplitterHandle(self.orientation(), self)

        return self.split_handle

    def addLayout(self, layout: QLayout) -> QWidget:
        layout_wrapper = QWidget()
        layout_wrapper.setLayout(layout)

        super().addWidget(layout_wrapper)

        return layout_wrapper

    def addWrappedWidget(self, widget: QWidget) -> None:
        wrapper_layout = QVBoxLayout()
        wrapper_layout.addWidget(widget)

        self.addLayout(wrapper_layout)
