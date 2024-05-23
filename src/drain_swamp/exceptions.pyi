__all__ = (
    "PyProjectTOMLParseError",
    "BackendNotSupportedError",
    "PyProjectTOMLReadError",
    "MissingRequirementsFoldersFiles",
)

class PyProjectTOMLReadError(OSError):
    def __init__(self, msg: str) -> None: ...

class PyProjectTOMLParseError(ValueError):
    def __init__(self, msg: str) -> None: ...

class BackendNotSupportedError(ValueError):
    def __init__(self, msg: str) -> None: ...

class MissingRequirementsFoldersFiles(AssertionError):
    def __init__(self, msg: str) -> None: ...
