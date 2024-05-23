from pathlib import Path
from typing import Any

__all__ = ("get_pyproject_toml",)

def get_pyproject_toml(path_config: Path | str) -> dict[str, Any]: ...
def get_d_pyproject_toml(path: Any | None) -> dict[str, Any] | None: ...
