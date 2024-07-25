from collections.abc import Callable
from typing import Any

import setuptools

def version_keyword(
    dist: setuptools.Distribution,
    keyword: str,
    value: bool | dict[str, Any] | Callable[[], dict[str, Any]],
) -> None: ...
