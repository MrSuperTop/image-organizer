from pathlib import Path

from ui.path_utils.absolute_paths import absolute_paths


class SamePathError(ValueError):
    @absolute_paths
    def __init__(self, to_move: Path, move_to: Path, *args: object) -> None:
        self.to_move = to_move
        self.move_to = move_to


        super().__init__(
            f'The paths for "to_move" and "move_to" may not be identical but "{str(to_move)}" and "{str(move_to)}" are the same',
            *args
        )


class IsNotADirectoryError(ValueError):
    @absolute_paths
    def __init__(self, path: Path, *args: object) -> None:
        self.path = path
        super().__init__(f'"{str(self.path)}" is not a directory', *args)


class NoImagesFoundError(ValueError):
    @absolute_paths
    def __init__(self, path: Path | list[Path], *args: object) -> None:
        parts = ['No images where found']
        if isinstance(path, Path):
            parts.append(f'in "{str(path)}"')

        message = ' '.join(parts)
        super().__init__(message, *args)
