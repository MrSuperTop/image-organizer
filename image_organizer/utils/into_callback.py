from asyncio.futures import Future
from collections.abc import Callable
from typing import Concatenate, ParamSpec, TypeVar

T = TypeVar('T')
HandlerSpec = ParamSpec('HandlerSpec')
RT = TypeVar('RT')


def into_callback(
    handler: Callable[Concatenate[T, HandlerSpec], RT],
    *args: HandlerSpec.args,
    **kwargs: HandlerSpec.kwargs
) -> Callable[[Future[T]], RT]:
    def callback(result_future: Future[T]) -> RT:
        result = result_future.result()
        return handler(result, *args, **kwargs)

    return callback
