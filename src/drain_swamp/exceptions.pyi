__all__ = (
    "PyProjectTOMLParseError",
    "PyProjectTOMLReadError",
    "MissingRequirementsFoldersFiles",
)

class PyProjectTOMLReadError(OSError):
    def __init__(self, msg: str) -> None: ...

class PyProjectTOMLParseError(ValueError):
    def __init__(self, msg: str) -> None: ...

class MissingRequirementsFoldersFiles(AssertionError):
    def __init__(self, msg: str) -> None: ...
