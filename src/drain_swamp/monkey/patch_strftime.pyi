import abc
import datetime

__all__ = ("StrFTime",)

class Patch(abc.ABC):
    @abc.abstractmethod
    def __call__(self, dt_a: datetime.datetime, str_part: str) -> str: ...

class PatchLeadingDay(Patch):
    AFFECTED_TOKEN: str = ...
    AFFECTS: bool = ...
    def __call__(self, dt_a: datetime.datetime, str_part: str) -> str: ...

class PatchAggregateD(Patch):
    AFFECTED_TOKEN: str = ...
    AFFECTS: bool = ...
    def __call__(self, dt_a: datetime.datetime, str_part: str) -> str: ...

class PatchAggregateT(Patch):
    AFFECTED_TOKEN: str = ...
    AFFECTS: bool = ...

    def __call__(self, dt_a: datetime.datetime, str_part: str) -> str: ...

class StrFTime:
    patches: tuple[type[Patch], ...] = ...

    def __init__(self, dt: datetime.datetime) -> None: ...
    @classmethod
    def fix_strftime_input(cls, dt_a: datetime.datetime, strftime_str: str) -> str: ...
    def strftime(self, format_: str) -> str: ...
