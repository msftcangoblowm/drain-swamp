PRETEND_KEY: str
PRETEND_KEY_NAMED: str

__all__ = ("normalize_dist_name",)

def normalize_dist_name(dist_name: str) -> str: ...
def read_named_env(
    *,
    tool: str = ...,
    name: str,
    dist_name: str | None,
) -> str | None: ...
def _scm_key(dist_name: str) -> str: ...
