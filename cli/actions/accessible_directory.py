import argparse
import os
from argparse import ArgumentError, ArgumentParser, Namespace
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import NoReturn

ERROR_MESSAGE_BASE = 'The path for {dest} {message}'


# TODO: Additional rules which can be provided in a form of an enum to the __init__, in this particular case there is a need to forbid any of the directories provided as the "move_to" to be the save as os.getcwd()
class AccessibleDirectory(argparse.Action):
    def _raise_error(self, message: str) -> NoReturn:
        raise ArgumentError(
            self,
            ERROR_MESSAGE_BASE.format(
                dest=self.dest,
                message=message
            )
        )

    def _check_accessibility(self, path: Path) -> None:
        exceptions: list[ArgumentError] = []
        checks: dict[str, Callable[[], bool]]= {
            'readable': lambda: os.access(path, os.R_OK),
            'writable': lambda: os.access(path, os.W_OK)
        }

        for message, check_func in checks.items():
            if check_func():
                continue

            exceptions.append(
                ArgumentError(
                    self,
                    f'Directory provided for {self.dest} is not {message}'
                )
            )

        if len(exceptions) > 0:
            raise ExceptionGroup(
                f'The directory at {path} for {self.dest} does not seem to be fully accessible',
                exceptions
            )

    def _run_checks(self, value: Path) -> Path:
        if not value.exists():
            self._raise_error(f'{value} is invalid')

        if not value.is_dir() and value.exists():
            self._raise_error(
                f'{value} is a path not to a directory, but a file'
            )

        self._check_accessibility(value)
        return value

    def _none_error(self) -> NoReturn:
        self._raise_error('may not be None')

    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: Path | Sequence[Path] | None,
        option_string: str | None = None
    ) -> None:
        if values is None:
            self._none_error()

        if isinstance(values, Sequence):
            result_value = list(map(self._run_checks, values))
        else:
            result_value = self._run_checks(values)

        setattr(namespace, self.dest, result_value)
