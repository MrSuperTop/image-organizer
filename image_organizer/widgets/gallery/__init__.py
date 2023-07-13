import asyncio
from asyncio.tasks import Task
from collections.abc import Sequence
from typing import Final

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget
from sqlalchemy import select

from image_organizer.db import session
from image_organizer.db.models.image import Image
from image_organizer.db.models.tag import Tag
from image_organizer.image_utils.load_and_resize import Dimentions
from image_organizer.image_utils.pixmap_cache import PixmapCache
from image_organizer.widgets.gallery.gallery_image import GalleryImage

DESIRED_WIDTH = 3
IMAGE_HEIGTH_TO_WIDTH_RATION: Final[float] = 9 / 16

class Gallery(QWidget):
    def __init__(
        self,
        cache: PixmapCache,
        default_tag: Tag | None = None,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.grid_width = DESIRED_WIDTH
        image_width = self.width() // self.grid_width
        self.image_dimetions = Dimentions(
            image_width,
            int(image_width * IMAGE_HEIGTH_TO_WIDTH_RATION)
        )

        self.cache = cache
        self._image_containers: list[GalleryImage] = []

        self.gui()

        asyncio.ensure_future(self.update_images(default_tag))

    def gui(self) -> None:
        self._layout = QVBoxLayout()

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()

        self.label = QLabel('Images')

        # TODO: Consider this https://doc.qt.io/qtforpython-6/examples/example_widgets_layouts_flowlayout.html
        self.images_grid = QHBoxLayout()
        self.images_grid.addStretch()

        scroll_layout.addWidget(self.label)
        scroll_layout.addLayout(self.images_grid)

        self.setLayout(self._layout)

        scroll_content.setLayout(scroll_layout)
        self.scroll_area.setWidget(scroll_content)
        self._layout.addWidget(self.scroll_area)

    async def update_images(self, tag: Tag | None) -> None:
        if tag is None:
            images_query = select(Image)
        else:
            images_query = select(Image) \
                .join(Tag, Tag.image_id == Image.id) \
                .where(Tag.id == tag.id)

        self.images: Sequence[Image] = session.scalars(images_query).all()

        rows_number = len(self.images) // self.grid_width + 1
        images_iter = iter(self.images)
        containers_iter = iter(self._image_containers)
        tasks: list[Task[None]] = []

        # TODO: Make the number of images in each row variable with scaling
        for _ in range(self.grid_width):
            column_layout = QVBoxLayout()
            column_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            for _ in range(rows_number):
                try:
                    next_container = next(containers_iter)
                except StopIteration:
                    next_container = GalleryImage(self.image_dimetions, self.cache)

                try:
                    # TODO: Load in only the images which are in the view or are close to the user view
                    set_task = asyncio.Task(
                        next_container.set_image(next(images_iter))
                    )

                    tasks.append(set_task)
                except StopIteration:
                    # TODO: Insert a proper spacer instead of stupidly running the loop. I wasn't able to figure out the sapcings unfortunately
                    ...

                column_layout.addWidget(next_container)

            self.images_grid.addLayout(column_layout)

        self.images_grid.addStretch()
