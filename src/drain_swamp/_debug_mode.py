"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Control when logging should be printed When to have Turn on logging repr helpers. Careful to use PurePath subclasses

.. py:data:: __all__
   :type: tuple[str]
   :value: ("set_debug_mode",)

   Module's exports

"""

import sys
from logging.config import dictConfig
from unittest.mock import patch

__all__ = ("set_debug_mode",)


def set_debug_mode(*, is_ci=False):
    """Turn on debug mode, which should print message to stdout.

    Normally code debugging is done thru a tests suite. That might not
    be an option when **critical** code is executed by CI/CD.

    Use on either:

    - one entrypoint command

    - entire entrypoint

    Turn ``__debug__`` flag off by executing entrypoint with python options:
    ``-0`` or ``-00``

    :param is_ci: Default False. App level flag. True to turn on debug mode
    :type is_ci: bool
    """
    # Situational flags. Seperate with OR logic
    is_situation = is_ci is True

    # Negative condition flags
    is_pytest = "pytest" in sys.modules
    is_coverage = "coverage" in sys.modules
    is_testing = is_pytest or is_coverage

    is_debug_mode = __debug__ and is_situation and not is_testing

    if is_debug_mode:  # pragma: no cover
        with patch("drain_swamp.constants.IS_TESTING", return_value=True):
            from .constants import LOGGING

            dictConfig(LOGGING)
    else:  # pragma: no cover
        pass
