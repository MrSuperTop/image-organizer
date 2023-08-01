from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QProgressDialog, QWidget


# TODO: More information
class DistributionProgressDialog(QProgressDialog):
    def __init__(
        self,
        to_distribute_count: int,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(
            'Distributing...',
            'Abort',
            0,
            to_distribute_count + 1,
            parent
        )

        self.failed = 0
        self.progress = 0

        self.setWindowTitle('Distribution progress')
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumDuration(0)

    @property
    def moved(self) -> int:
        return self.progress - self.failed

    def update_status(self) -> None:
        self.progress += 1
        self.setValue(self.progress)

    def update_status_failed(self) -> None:
        self.failed += 1
        self.update_status()
