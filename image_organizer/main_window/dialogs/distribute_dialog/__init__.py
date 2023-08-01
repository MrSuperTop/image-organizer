import os
import shutil
from itertools import count
from pathlib import Path
from time import perf_counter

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import and_, func, select

from image_organizer.db import session
from image_organizer.db.models.image import Image
from image_organizer.db.models.tag import Tag
from image_organizer.main_window.dialogs.distribute_dialog.distribution_progress_dialog import (
    DistributionProgressDialog,
)
from image_organizer.pixmap_cache import PixmapCache
from image_organizer.utils.format_strings import format_strings
from ui.path_utils.absolute_paths import absolute_paths

Moved = int
Failed = int

@absolute_paths
def distribute_images(
    to_distribute: list[Image],
    destination: Path,
    cache_to_update: PixmapCache,
    progress_dialog_parent: QWidget
) -> tuple[Moved, Failed]:
    if not destination.exists():
        raise ValueError('Export destination does not exist')

    if not destination.is_dir():
         raise ValueError('Export destination directory is not a folder')

    # FIXME: Try to move this somewhere, better separation of concerns
    progress_dialog = DistributionProgressDialog(
        len(to_distribute),
        progress_dialog_parent
    )

    # FIXME: Implement with ThreadPoolExecutor
    for image in to_distribute:
        if progress_dialog.wasCanceled():
            break

        to_move = image.format_path()
        if not to_move.exists():
            progress_dialog.update_status_failed()
            continue

        # TODO: An option to group images, based not only on the simple concatination of the tags' names but by taking into account each tag's popularity and creating subfolders for less popular tags
        sorted_names = sorted(map(lambda tag: tag.name, image.tags))
        combined_name = '_'.join(sorted_names)
        output_folder = destination.joinpath(combined_name).absolute()

        if not output_folder.exists():
            output_folder.mkdir()

        as_moved_path = output_folder.joinpath(to_move.name)
        original_path = as_moved_path
        for i in count():
            if not as_moved_path.exists():
                break

            new_name = f'{original_path.stem}-{i}-{"".join(original_path.suffixes)}'
            as_moved_path = original_path.with_name(new_name)

        shutil.move(to_move, as_moved_path)
        progress_dialog.update_status()

        # TODO: Abstract the logic of updating the cache away, apply the same updates on individual image moves
        cache_to_update.update_path(to_move, as_moved_path)
        image.path = Image.path_formatter(as_moved_path)

    session.commit()
    return progress_dialog.moved, progress_dialog.failed


# TODO: Consider an option for a dry run
# TODO: Keep track of distributions history, automatically select the last export directory
# TODO: Option to copy the images

class DistributeDialog(QDialog):
    @absolute_paths
    def __init__(
        self,
        pixmap_cache: PixmapCache,
        distribute_from: Path | None = None,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self._pixmap_cache = pixmap_cache
        self.distribute_from = distribute_from
        self.destination: Path | None = None

        relative_images_with_tags_query = select(Image) \
            .join(
                Tag,
                and_(
                    Tag.image_id == Image.id,
                    Image.path.startswith(str(distribute_from))
                )
            )

        relative_images_with_tags = session \
            .scalars(relative_images_with_tags_query) \
            .unique()

        self.to_distribute = list(relative_images_with_tags)

        self._layout = self.gui(self.to_distribute)
        self.setLayout(self._layout)

    def gui(self, discovered: list[Image]) -> QVBoxLayout | QHBoxLayout:
        self._no_destination_message = QMessageBox(self)
        self._no_destination_message.setText('Please select the destination folder')

        self.setWindowTitle('Distribute')

        self._folder_dialog = QFileDialog(
            self,
            'Select the distributing folder',
            os.getcwd()
        )

        self._folder_dialog.setFileMode(QFileDialog.FileMode.Directory)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignJustify)

        settings_layout = QVBoxLayout()
        settings_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )

        info_label = QLabel()
        total_images_count_query = select(func.count()).select_from(Image)

        total_images_count = session.execute(total_images_count_query).scalar()
        if total_images_count is None:
            count_string = None
        elif total_images_count == len(discovered):
            count_string = '(all)'
        else:
            count_string = f'({total_images_count} total)'

        info_label.setText(
            format_strings((
                f'{len(discovered)} image(s) to distribute',
                count_string
            ))
        )

        settings_layout.addWidget(info_label)

        destination_select_layout = QVBoxLayout()
        destination_select_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )

        self._destination_label = QLabel()
        self._destination_label.setText('(Not selected)')

        self._select_destination_button = QPushButton('Select destination')
        self._select_destination_button.setMaximumWidth(150)
        self._select_destination_button.clicked.connect(self._open_select_folder_dialog)

        destination_select_layout.addWidget(self._destination_label)
        destination_select_layout.addWidget(self._select_destination_button)

        settings_layout.addLayout(destination_select_layout)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        self.buttons.accepted.connect(self._distribute_handler)
        self.buttons.rejected.connect(self.reject)

        layout.addLayout(settings_layout)
        layout.addWidget(self.buttons)

        return layout

    def _open_select_folder_dialog(self) -> None:
        exec_result = self._folder_dialog.exec()

        if exec_result == QDialog.DialogCode.Rejected:
            return

        selected = self._folder_dialog.selectedFiles()
        if len(selected) != 1:
            return

        self.destination = Path(selected[0])
        self._destination_label.setText(str(self.destination))

    def _distribute_handler(self) -> None:
        if self.destination is None:
            self._no_destination_message.exec()
            return

        start = perf_counter()
        moved, failed = distribute_images(
            self.to_distribute, self.destination,
            self._pixmap_cache, self
        )

        diff = perf_counter() - start

        QMessageBox.information(
            self,
            'Distribution completed',
            format_strings(
                f'Moved {moved}/{len(self.to_distribute)} image(s), (failed {failed})',
                f'In {round(diff, 3)} s'
            )
        )

        self.accept()
