import os
from pathlib import Path

from PIL import Image

exts = Image.registered_extensions()
supported_extensions = {ex for ex, f in exts.items() if f in Image.OPEN}


def find_images(folder_path_or_glob: Path | str) -> list[Path]:
    if isinstance(folder_path_or_glob, Path):
        files = folder_path_or_glob.iterdir()
    else:
        files = Path(os.getcwd()).glob(folder_path_or_glob)

    result: list[Path] = []
    for item in files:
        if item.suffix not in supported_extensions:
            continue

        result.append(item)

    return result
