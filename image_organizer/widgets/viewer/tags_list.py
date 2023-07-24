from __future__ import annotations

import typing

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import delete

from image_organizer.db import session
from image_organizer.db.models.image import Image
from image_organizer.db.models.tag import Tag
from ui.entry_list import EntryList
from ui.folder_viewer import ImageChangedData
from ui.list_with_menu import ContextMenuSelectedData

if typing.TYPE_CHECKING:
    from image_organizer.widgets.viewer import Viewer


# TODO: Sort the tags in the order of popularity
# TODO: use QListWidgetItem.addData to bind the Tag objects
class TagsList(EntryList):
    new_tag_added = pyqtSignal(str)
    tag_removed = pyqtSignal(str)

    def __init__(
        self,
        connected_viewer: Viewer,
        parent: QWidget | None = None
    ) -> None:
        tag_names = Tag.distinct_tag_names(session)

        self._viewer = connected_viewer
        self._viewer.image_changed.connect(self._image_changed_handler)

        self._is_synced = True

        self.current_image: Image
        self.current_tags: dict[str, Tag] = {}

        super().__init__(
            tag_names,
            parent=parent
        )

    def gui(self) -> QVBoxLayout | QHBoxLayout:
        layout = super().gui()

        self.list.itemPressed.connect(self._select_handler)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.list.add_action(self.list.remove_action, self._remove_handler)

        self.label = QLabel('Image tags')
        layout.insertWidget(0, self.label)

        self.save_button = QPushButton('Save tags')
        self.save_button.clicked.connect(self.save_if_not)
        self.save_button.setDisabled(True)
        layout.addWidget(self.save_button)

        return layout

    @property
    def is_synced(self) -> bool:
        return self._is_synced

    @is_synced.setter
    def is_synced(self, new_value: bool) -> None:
        self._is_synced = new_value
        self.save_button.setDisabled(self._is_synced)

    def save_if_not(self):
        if not self.is_synced:
            session.commit()
            self.is_synced = True

    def sync_tags(self, changed_data: ImageChangedData) -> None:
        self.save_if_not()

        self.current_image = changed_data.image
        self.current_tags = {tag.name: tag for tag in changed_data.image.tags}

    def _add_handler(self) -> None:
        tag_name = self.entry_field.text()
        if tag_name in self.present_entries:
            return

        super()._add_handler()
        self.new_tag_added.emit(tag_name)

    def _update_list_selection(self, tags: dict[str, Tag]) -> None:
        self.list.clearSelection()

        to_select_names = set(
            [tag.name for tag in tags.values() if tag.is_selected]
        )

        items = [self.list.item(index) for index in range(self.list.count())]
        to_select = [item for item in items if item.text() in to_select_names]

        for item in to_select:
            item.setSelected(True)

    def _image_changed_handler(self, changed_data: ImageChangedData) -> None:
        self.sync_tags(changed_data)
        self._update_list_selection(self.current_tags)

    def _select_handler(self, selected_item: QListWidgetItem):
        selected_name = selected_item.text()

        if selected_name not in self.current_tags:
            selected_tag = Tag(
                name=selected_name,
                image_id=self.current_image.id,
                is_selected=selected_item.isSelected()
            )

            session.add(selected_tag)
            self.current_image.tags.append(selected_tag)
            self.current_tags[selected_tag.name] = selected_tag
        else:
            selected_tag = self.current_tags[selected_name]

        selected_tag.is_selected = selected_item.isSelected()
        self.is_synced = False

    def _remove_handler(
        self,
        signal_data: ContextMenuSelectedData[QListWidgetItem]
    ) -> None:
        to_remove = signal_data.affected_item

        self.save_if_not()

        to_remove_name = to_remove.text()
        delete_tag_query = delete(Tag).where(Tag.name == to_remove.text())
        session.execute(delete_tag_query)

        del self.current_tags[to_remove_name]
        find_iter = (
            index for index, tag in enumerate(self.current_image.tags)
            if tag.name == to_remove_name
        )

        found_index = next(find_iter, None)
        if found_index is not None:
            self.current_image.tags.pop(found_index)

        self.tag_removed.emit(to_remove_name)
