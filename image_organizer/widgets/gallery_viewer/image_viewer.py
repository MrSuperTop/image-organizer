from PyQt6 import QtCore, QtGui, QtWidgets

# TODO: Load in higher res images as it it goes deeper.
# TODO: Support for raw files using https://rawkit.readthedocs.io/en/v0.6.0/api/rawkit.html


class ImageViewer(QtWidgets.QGraphicsView):
    photoClicked = QtCore.pyqtSignal(QtCore.QPointF)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._shown = False
        self._zoom = 0
        self._empty = True
        self._scene = QtWidgets.QGraphicsScene(self)

        self._photo = QtWidgets.QGraphicsPixmapItem()

        self._text = QtWidgets.QGraphicsTextItem('No images...')

        self._text.hide()
        default_font = self._text.font()
        default_font.setPointSize(52)
        self._text.setFont(default_font)
        self._text_rect = self._text.boundingRect()

        self._scene.addItem(self._photo)
        self._scene.addItem(self._text)

        self._update_text_dimentions()

        self.setScene(self._scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

    def _update_text_dimentions(self):
        self._text.setPos(
            int(self._scene.width() / 2 - self._text_rect.width() / 2),
            int(self._scene.height() / 2 - self._text_rect.height() / 2)
        )

    def fitInView( # pyright: ignore[reportIncompatibleMethodOverride]
        self,
    ) -> None:
        rect = QtCore.QRectF(self._photo.pixmap().rect())

        if not rect.isNull():
            self.setSceneRect(rect)

            if not self._empty:
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0

    def setPhoto(self, pixmap: QtGui.QPixmap | None = None):
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
            self._photo.setPixmap(pixmap)

            self._photo.show()
            self._text.hide()
        else:
            self.fitInView()

            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())

            self._photo.hide()
            self._text.show()

        if self._shown:
            self.fitInView()

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        if self._empty:
            return

        if event.angleDelta().y() > 0:
            factor = 1.25
            self._zoom += 1
        else:
            factor = 0.8
            self._zoom -= 1

        if self._zoom == 0:
            self.fitInView()
        else:
            self.scale(factor, factor)

    def toggleDragMode(self) -> None:
        if self.dragMode() == QtWidgets.QGraphicsView.DragMode.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._photo.isUnderMouse():
            self.photoClicked.emit(self.mapToScene(event.position().toPoint()))

        super().mousePressEvent(event)

    def showEvent(self, event: QtGui.QShowEvent):
        if not self._shown:
            self._shown = True
            self.fitInView()

        self._update_text_dimentions()
        super().showEvent(event)
