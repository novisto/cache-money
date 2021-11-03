import inspect
from typing import Callable


def decode(s):
    return s.decode("utf-8") if isinstance(s, bytes) else s


def get_function_path(fn: Callable) -> str:
    return f"{inspect.getmodule(fn).__name__}.{fn.__name__}"
