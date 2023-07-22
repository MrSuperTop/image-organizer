import os
from pathlib import Path
from typing import Literal

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.paths_list import PathsList


class ForbiddenPathError(ValueError):
    def __init__(self, message: str, reason: str, *args: object) -> None:
        self.message = message
        self.reason = reason

        super().__init__(*args)


class NotUniquePathError(ValueError):
    ...


Rule = tuple[Path | list[Path], str]
Rules = list[Rule]
ForbiddenFoldersFilter = Rules | None


def format_forbidden_folders(
    forbidden_folders: Rules
) -> Rules:
    formatted: Rules = []
    for rule in forbidden_folders:
        paths, message = rule
        if len(message) == 0:
            continue

        first_word, sep, remainder = message.partition(' ')
        formatted_message = f'{first_word[0].lower()}{first_word[1:]}{sep}{remainder}'

        formatted.append((paths, formatted_message))

    return formatted


class FoldersList(QWidget):
    move_to_changed = pyqtSignal(Path)

    def __init__(
        self,
        start_selection: Path | None = None,
        forbidden_folders: ForbiddenFoldersFilter = None,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.folders: set[Path] = set()

        self.forbidden_folders: ForbiddenFoldersFilter = None
        if forbidden_folders is not None:
            self.forbidden_folders = format_forbidden_folders(forbidden_folders)

        self.gui()

        if start_selection is not None:
            self.add_folder(start_selection)
            self._paths_list.setCurrentRow(0)

    def gui(self) -> None:
        self._layout = QVBoxLayout()

        self._paths_list = PathsList(
            mininum_lenght=1
        )

        self._paths_list.itemSelectionChanged.connect(self._selection_handler)

        self._buttons_layout = QHBoxLayout()

        self._add_folder_button = QPushButton('Add folder')
        self._add_folder_button.clicked.connect(self._add_folder_handler)

        self._buttons_layout.addWidget(self._add_folder_button)

        self._msg_box = QMessageBox(
        )
        self._msg_box.setIcon(QMessageBox.Icon.Warning)

        self._layout.addWidget(self._paths_list)
        self._layout.addLayout(self._buttons_layout)

        self.setLayout(self._layout)


    def _selection_handler(self) -> None:
        selected = self._paths_list.selectedItems()[0]
        path_data: Path = selected.data(Qt.ItemDataRole.UserRole)

        self.move_to_changed.emit(path_data)

    def _is_forbidden_path(
        self,
        to_check: Path
        ) -> tuple[Literal[False], None ] | tuple[Literal[True], str]:
        if self.forbidden_folders is None:
            return False, None

        for paths, message in self.forbidden_folders:
            if isinstance(paths, list):
                for path in paths:
                    if path == to_check:
                        return True, message
            else:
                if paths == to_check:
                    return True, message

        return False, None

    def add_folder(self, folder_path: Path) -> None:
        if folder_path in self.folders:
            raise NotUniquePathError('This path is already present in the list')

        is_allowed, forbidden_message = self._is_forbidden_path(folder_path)

        # The None check is required as pyright does not understand that the function
        # either returns a tuple[Literal[True], None] or tuple[Literal[False], str]
        # and merges everyting into a type like this: tuple[bool, str | None].
        # I am not sure how not prevent this behaviour and it is even possible.
        # I think it has to do something with how pyright handles type narrowing.

        if not is_allowed and forbidden_message is not None:
            raise ForbiddenPathError(
                'This path can not be added',
                forbidden_message
            )

        self.folders.add(folder_path)
        self._paths_list.add_path(folder_path)

    # TODO: Implement a custom QSortFilterProxyModel
    # https://stackoverflow.com/questions/27955403/how-to-use-qsortfilterproxymodels-setfilterregexp-along-with-filteracceptsrow
    # https://doc.qt.io/qt-6/qsortfilterproxymodel.html#filterAcceptsRow
    def _add_folder_handler(self) -> None:
        file_dialog = QFileDialog(
            self,
            'Select folder',
            os.getcwd()
        )

        file_dialog.setFileMode(QFileDialog.FileMode.Directory)

        result = file_dialog.exec()
        if not result:
            return

        selected = file_dialog.selectedFiles()
        if len(selected) != 1:
            return

        folder_path = Path(selected[0])

        try:
            self.add_folder(folder_path)
        except NotUniquePathError:
            self._msg_box.setText(
                'You are trying to add an already present directory'
            )

            self._msg_box.exec()
        except ForbiddenPathError as e:
            self._msg_box.setText(
                f'This directory can not be added as {e.reason}'
            )

            self._msg_box.exec()
