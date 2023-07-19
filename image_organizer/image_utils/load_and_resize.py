from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps
from PyQt6.QtGui import QImage, QPixmap


@dataclass(frozen=True, eq=True)
class Dimentions:
    width: int
    height: int

    @property
    def size(self) -> tuple[int, int]:
        return self.width, self.height


def pil2pixmap(image: Image.Image):
    if image.mode == 'RGB':
        r, g, b = image.split()
        image = Image.merge('RGB', (b, g, r))
    elif image.mode == 'RGBA':
        r, g, b, a = image.split()
        image = Image.merge('RGBA', (b, g, r, a))
    elif image.mode == 'L':
        image = image.convert('RGBA')

    # * Ignoring, as the stubs for Pillow do not specify a type
    data = image.convert('RGBA').tobytes('raw', 'RGBA') # pyright: ignore[reportUnknownMemberType]

    qim = QImage(data, *image.size, QImage.Format.Format_ARGB32)
    pixmap = QPixmap.fromImage(qim)

    return pixmap


def load_and_resize(image_path: Path, max_dimensions: Dimentions) -> QPixmap | None:
    if not image_path.exists():
        return

    with Image.open(image_path) as image:
        image = ImageOps.exif_transpose(image)
        ratio = min(
            max_dimensions.width / image.width,
            max_dimensions.height / image.height
        )

        if ratio != 1:
            new_size = int(image.width * ratio), int(image.height * ratio)
            image = image.resize(new_size, Image.Resampling.BILINEAR)

        pixmap = pil2pixmap(image)
        return pixmap
