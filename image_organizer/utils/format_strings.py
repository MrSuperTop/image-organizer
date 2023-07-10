from collections.abc import Iterable
from typing import TypeGuard, TypeVar

SubString = str | None | Iterable[str | None]
T = TypeVar('T')


def filter_out_none(item: T | None) -> TypeGuard[T]:
    return item is not None


def format_strings(
    *strings: SubString
) -> str:
    lines: list[str] = []
    for item in strings:
        if item is None:
            continue

        if isinstance(item, str):
            lines.append(item)
            continue

        new_line = ' '.join(filter(filter_out_none, item))
        lines.append(new_line)

    return '\n'.join(lines)
