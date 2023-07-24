from collections.abc import Callable
from pathlib import Path
from typing import Any, ParamSpec, TypeVar

RT = TypeVar('RT')
DecoratedSpec = ParamSpec('DecoratedSpec')


def absolute_paths(func: Callable[DecoratedSpec, RT]) -> Callable[DecoratedSpec, RT]:
    def wrapper(*args: tuple[object], **kwargs: dict[str, object]) -> RT:
        checked_args: list[Any] = []
        for arg in args:
            if isinstance(arg, Path):
                arg = arg.absolute()

            checked_args.append(arg)

        # * Ignoring as PEP612 does not seem to provide a proper way to mutate the ParamSpec.args in a type-safe way
        # https://stackoverflow.com/questions/71362488/apply-transformation-on-a-paramspec-variable
        # https://peps.python.org/pep-0612/

        return func(*checked_args, **kwargs) # pyright: ignore[reportGeneralTypeIssues]
    return wrapper # pyright: ignore[reportGeneralTypeIssues]
