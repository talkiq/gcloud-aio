from typing import Any
from typing import Callable
from typing import Iterator
from typing import Optional
from typing import TypeVar


F = TypeVar('F', bound=Callable[..., Any])


def expo(base: float = ..., factor: float = ...,
         max_value: Optional[float] = ...) -> Iterator[float]:
    ...

def on_exception(wait_gen: Callable[..., Iterator[float]],
                 exception: type,
                 max_tries: int = ...) -> Callable[[F], F]:
    ...
