from __future__ import annotations

import typing

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QWidget
from sqlalchemy import select

from image_organizer.db import session
from image_organizer.db.models.image import Image
from image_organizer.db.models.tag import Tag
from ui.entry_list import EntryList

if typing.TYPE_CHECKING:
    from image_organizer.widgets.taggable_folder_viewer import TaggableFolderViewer


class TagsList(EntryList):
    new_tag_added = pyqtSignal(str)

    def __init__(
        self,
        connected_viewer: TaggableFolderViewer,
        parent: QWidget | None = None
    ) -> None:
        self.tags = Tag.distinct_tag_names(session)
        self.viewer = connected_viewer
        self.current_image: Image

        super().__init__(
            self.tags,
            parent=parent
        )

        self.list.itemActivated.connect(self._select_handler)

    def gui(self, *before_widgets: QWidget) -> None:
        self.label = QLabel('Image tags')

        super().gui(self.label, *before_widgets)

        self.viewer.image_changed.connect(self._image_change_handler)
        self.list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

    def _add_handler(self) -> None:
        text = self.entry_field.text()

        if text in self.possible_entries:
            return

        new_tag = Tag(
            name=text,
            image=self.current_image
        )

        session.add(new_tag)
        session.commit()

        self.tags.append(new_tag.name)
        self.new_tag_added.emit(new_tag.name)

        super()._add_handler()

    def _image_change_handler(self, new_image: Image) -> None:
        self.current_image = new_image

        self.list.clearSelection()

        for tag in new_image.tags:
            if not tag.is_selected:
                continue

            try:
                tag_index = self.tags.index(tag.name)
            except ValueError:
                continue

            self.list.setCurrentRow(tag_index)

    def _select_handler(self, changed_item: QListWidgetItem):
        changed_tag_text = changed_item.text()
        changed_tag_query = select(Tag).where(
            Tag.name == changed_tag_text,
            Tag.image_id == self.current_image.id
        )

        changed_tag = session.scalars(changed_tag_query).one_or_none()
        if changed_tag is not None:
            changed_tag.is_selected = changed_item.isSelected()
            session.commit()

            return

        new_tag = Tag(
            name=changed_tag_text,
            image=self.current_image,
            is_selected=changed_item.isSelected()
        )

        self.current_image.tags.append(new_tag)
        session.commit()
