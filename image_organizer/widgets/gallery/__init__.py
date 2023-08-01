import asyncio
from asyncio.tasks import Task
from collections.abc import Sequence
from typing import Final

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import delete, select, true

from image_organizer.db import session
from image_organizer.db.models.image import Image
from image_organizer.db.models.tag import Tag
from image_organizer.image_utils.load_and_resize import Dimentions
from image_organizer.pixmap_cache import PixmapCache
from image_organizer.widgets.gallery.gallery_image import GalleryImage
from image_organizer.widgets.viewer.tags_list import TagsList

DESIRED_WIDTH = 3
IMAGE_HEIGTH_TO_WIDTH_RATION: Final[float] = 9 / 16
EVERYTHING_VARIANT = 'All images'


# TODO: Isolate the tag selector + use Tag objects instead of strings everywhere
class Gallery(QWidget):
    def __init__(
        self,
        cache: PixmapCache,
        tags_list: TagsList,
        default_tag: Tag | None = None,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        tags_list.new_tag_added.connect(self._new_tag_added_handler)
        tags_list.tag_removed.connect(self._tag_removed_handler)
        self.tags_list = tags_list

        self.preferred_grid_width = DESIRED_WIDTH
        image_width = self.width() // self.preferred_grid_width
        self.image_dimetions = Dimentions(
            image_width,
            int(image_width * IMAGE_HEIGTH_TO_WIDTH_RATION)
        )

        self.cache = cache
        self._image_containers: list[GalleryImage] = []
        self._column_layouts: list[QVBoxLayout] = []

        self.gui()

        self.tag_names = [EVERYTHING_VARIANT, *Tag.distinct_tag_names(session)]
        for name in self.tag_names:
            self.tags_selector.addItem(name)

        default_tag_name = getattr(default_tag, 'name', EVERYTHING_VARIANT)
        self.selected_tag_name = default_tag_name
        self.update_images(default_tag_name)

    def gui(self) -> None:
        self._layout = QVBoxLayout()

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()

        tags_selector_layout = QVBoxLayout()
        self.tags_label = QLabel('Select tag')
        self.tags_selector = QComboBox()
        self.tags_selector.activated.connect(self._selected_tag_change_handler)

        tags_selector_layout.addWidget(self.tags_label)
        tags_selector_layout.addWidget(self.tags_selector)

        gallery_layout = QVBoxLayout()
        self.images_label = QLabel('Images')

        # TODO: Consider this https://doc.qt.io/qtforpython-6/examples/example_widgets_layouts_flowlayout.html or come up with own solution
        self.images_grid = QHBoxLayout()
        self.images_grid.addStretch()
        self.images_grid.addStretch()

        gallery_layout.addWidget(self.images_label)
        gallery_layout.addLayout(self.images_grid)

        scroll_layout.addLayout(tags_selector_layout)
        scroll_layout.addLayout(gallery_layout)

        scroll_content.setLayout(scroll_layout)
        self.scroll_area.setWidget(scroll_content)
        self._layout.addWidget(self.scroll_area)

        self.setLayout(self._layout)

    async def _update_images(self, tag_name: str) -> None:
        # TODO: Make this a little bit more secure, user can just create the same tag
        if tag_name == EVERYTHING_VARIANT:
            images_query = select(Image)
        else:
            # TODO: Query only the images under the correct directory
            images_query = select(Image) \
                .join(Tag, Tag.image_id == Image.id) \
                .where(Tag.name == tag_name, Tag.is_selected == true())

        images: Sequence[Image] = session.scalars(images_query).unique().all()
        to_delete_ids: list[int] = []
        filtered_images: list[Image] = []
        for image in images:
            if not image.format_path().exists():
                to_delete_ids.append(image.id)
                continue

            filtered_images.append(image)

        delete_not_existent_query = delete(Image).where(Image.id.in_(to_delete_ids))
        session.execute(delete_not_existent_query)

        self.images = filtered_images

        # TODO: Start reusing the old containers and layouts, encapsulate the grid in a custom QLayout component + make resizable
        for container in self._image_containers:
            container.deleteLater()

        for layout in self._column_layouts:
            layout.deleteLater()

        self._image_containers = []
        self._column_layouts = []

        colums_number = min(self.preferred_grid_width, len(self.images))
        rows_number = len(self.images) // colums_number + 1 if len(self.images) > colums_number else 1
        images_iter = iter(self.images)
        containers_iter = iter(self._image_containers)
        tasks: list[Task[None]] = []

        # TODO: Make the number of images in each row variable with scaling
        for _ in range(colums_number):
            column_layout = QVBoxLayout()
            column_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self._column_layouts.append(column_layout)

            for _ in range(rows_number):
                try:
                    next_container = next(containers_iter)
                except StopIteration:
                    next_container = GalleryImage(self.image_dimetions, self.cache)
                    self._image_containers.append(next_container)

                try:
                    # TODO: Load in only the images which are in the view or are close to the user view
                    set_task = asyncio.Task(
                        next_container.set_image(next(images_iter))
                    )

                    tasks.append(set_task)
                except StopIteration:
                    # TODO: Insert a proper spacer instead of stupidly running the loop. I wasn't able to figure out the spacings unfortunately
                    ...

                column_layout.addWidget(next_container)

            self.images_grid.insertLayout(self.images_grid.count() - 1, column_layout)

    def update_images(self, tag_name: str) -> None:
        asyncio.create_task(self._update_images(tag_name))

    def _selected_tag_change_handler(self, tag_index: int) -> None:
        new_tag_name = self.tag_names[tag_index]

        if new_tag_name == self.selected_tag_name:
            return

        self.update_images(new_tag_name)
        self.selected_tag_name = new_tag_name

    def _new_tag_added_handler(self, new_tag: str) -> None:
        self.tag_names.append(new_tag)
        self.tags_selector.addItem(new_tag)

    def _tag_removed_handler(self, removed_tag: str) -> None:
        to_remove_index = self.tag_names.index(removed_tag)

        deleted_name = self.tag_names.pop(to_remove_index)
        if deleted_name == self.selected_tag_name:
            self.tags_selector.setCurrentIndex(0)
            self.tags_selector.activated.emit(0)

        self.tags_selector.removeItem(to_remove_index)
