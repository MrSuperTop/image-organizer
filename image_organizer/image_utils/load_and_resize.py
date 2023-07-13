from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps
from PyQt6.QtGui import QImage, QPixmap


@dataclass(frozen=True)
class Dimentions:
    x: int
    y: int

    def size(self) -> tuple[int, int]:
        return self.x, self.y


def pil2pixmap(image: Image.Image):
    if image.mode == "RGB":
        r, g, b = image.split()
        image = Image.merge("RGB", (b, g, r))
    elif  image.mode == "RGBA":
        r, g, b, a = image.split()
        image = Image.merge("RGBA", (b, g, r, a))
    elif image.mode == "L":
        image = image.convert("RGBA")

    image = ImageOps.exif_transpose(image)

    im2 = image.convert("RGBA")

    # * Ignoring, as the stubs for Pillow do not specify a type
    data = im2.tobytes("raw", "RGBA") # pyright: ignore[reportUnknownMemberType]
    qim = QImage(data, image.size[0], image.size[1], QImage.Format.Format_ARGB32)
    pixmap = QPixmap.fromImage(qim)

    return pixmap


def load_and_resize(image_path: Path, max_dimensions: Dimentions) -> QPixmap | None:
    if not image_path.exists():
        return

    with Image.open(image_path) as image:
        width, height = image.size
        ratio = min(max_dimensions.x / width, max_dimensions.y / height)

        if ratio != 1:
            new_size = int(width * ratio), int(height * ratio)
            image = image.resize(new_size, Image.Resampling.BILINEAR)

        pixmap = pil2pixmap(image)
        return pixmap
