from argparse import ArgumentError, ArgumentParser, Namespace
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from cli.actions.accessible_directory import AccessibleDirectory
from image_organizer.image_utils.find_images import find_images


class DirectoryOrGlob(AccessibleDirectory):
    def _raise_error(self, message: str) -> NoReturn:
        raise ArgumentError(
            self,
            message
        )

    def _run_path_checks(self, value: Path) -> Path:
        return super()._run_checks(value)

    def _run_glob_checks(self, pattern: str) -> list[Path]:
        glob_paths = find_images(pattern)

        if len(glob_paths) <= 0:
            self._raise_error(
                f'The glob pattern provided as {self.dest} did not match any images'
            )

        return glob_paths


    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: Path | Sequence[Path] | None,
        option_string: str | None = None
    ) -> None:
        if values is None:
            self._none_error()

        result: list[Path] | Path = []

        if isinstance(values, Path):
            single_path_or_glob = values

            if values.is_dir():
                result = self._run_path_checks(single_path_or_glob)
            else:
                result = self._run_glob_checks(str(single_path_or_glob))
        else:
            for value in values:
                if value.is_dir():
                    result.append(self._run_path_checks(value))
                else:
                    map(
                        lambda item: result.append(item),
                        self._run_glob_checks(str(value))
                    )

        setattr(namespace, self.dest, result)
