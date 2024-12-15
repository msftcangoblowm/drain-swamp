__all__ = (
    "PyProjectTOMLParseError",
    "PyProjectTOMLReadError",
)

class PyProjectTOMLReadError(OSError):
    def __init__(self, msg: str) -> None: ...

class PyProjectTOMLParseError(ValueError):
    def __init__(self, msg: str) -> None: ...
