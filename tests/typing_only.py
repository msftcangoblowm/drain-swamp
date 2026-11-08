"""
Used only during TYPE_CHECKING

"""

from contextlib import nullcontext as does_not_raise
from typing import (
    Never,
    NoneType,
    TypeAlias,
    Union,
)

try:
    from _pytest.python_api import RaisesContext  # noqa: F401
except (ModuleNotFoundError, ImportError):
    # docs say from 8.4+, but actually 8.3.5+
    #
    # Before `with block` can access: expectation.excinfo.[type|value]
    from _pytest.raises import RaisesExc as RaisesContext  # type: ignore[no-redef, import-not-found]  # noqa: F401

DOES_NOT_OR_DOES: TypeAlias = Union[does_not_raise[None], RaisesContext[BaseException]]

__all__ = (
    "DOES_NOT_OR_DOES",
    "Never",
    "NoneType",
    "TypeAlias",
)
