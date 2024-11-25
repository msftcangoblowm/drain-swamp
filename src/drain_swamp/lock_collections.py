"""
.. moduleauthor:: Dave Faulkmore <https://mastodon.social/@msftcangoblowme>

Load ``.in`` and ``.lock`` files once.

``.in`` files are never changed.

``.lock`` files are changed. So if cached, after writes, the cache
would have to be invalidated

.. py:data:: __all__
   :type: tuple[str, str]
   :value: ("Ins", "unlock_compile")

   Module exports

.. py:data:: is_module_debug
   :type: bool
   :value: False

   Toggle on/off module level logging

.. py:data:: _logger
   :type: logging.Logger

   Module level logger

"""

import copy
import dataclasses
import logging
import os
from collections.abc import (
    Collection,
    Iterator,
)
from pathlib import (
    Path,
    PurePath,
)

from .check_type import is_ok
from .constants import (
    SUFFIX_IN,
    SUFFIX_UNLOCKED,
    g_app_name,
)
from .exceptions import MissingRequirementsFoldersFiles
from .lock_datum import (
    InFileType,
    in_generic,
)
from .lock_filepins import (
    FilePins,
    get_path_cwd,
)
from .lock_loader import from_loader_filepins
from .lock_util import (
    ENDINGS,
    abspath_relative_to_package_base_folder,
    is_shared,
    replace_suffixes_last,
)
from .pep518_venvs import (
    VenvMapLoader,
    check_loader,
)

is_module_debug = False
_logger = logging.getLogger(f"{g_app_name}.lock_collections")
__all__ = (
    "Ins",
    "unlock_compile",
)


@dataclasses.dataclass
class Ins(Collection[FilePins]):
    """Store the ``.in`` :py:class:`~drain_swamp.lock_filepins.FilePins`.

    Previously ``Pins.from_loader``. Moved to lock_loader. Split into two
    implementations :py:class:`~drain_swamp.lock_loader.LoaderPin` and
    :py:class:`~drain_swamp.lock_loader.LoaderPinDatum`

    Benefits

    - FilePins.by_pkg get (PinDatum) by package name returns a list, rather than one
      More complex pins can be represented

      .. code-block:: text

         colorama<=1.5.0; python_version<="3.8"
         colorama>1.5.0, <=1.8.0; python_version>"3.8"; python_version<"3.10"
         colorama>1.8.0; python_version>="3.10"

    :ivar venv_path: Relative path to venv base folder. Acts as a key
    :vartype venv_path: typing.Any

    .. py:attribute:: loader
       :type: drain_swamp.pep518_venvs.VenvMapLoader

       Contains some paths and loaded not parsed venv reqs

    .. py:attribute:: _venv_relpath
       :type: str

       Relative path to venv base folder. Acts as a key

    .. py:attribute:: _file_pins
       :type: list[drain_swamp.lock_filepins.FilePins]

       Collection of PinDatum

    .. py:attribute:: _iter
       :type: collections.abc.Iterator[drain_swamp.lock_filepins.FilePins]

       Automatically reusable Iterator

    .. py:attribute:: _files
       :type: set[FilePins]

       Set of FilePins. Which contains the relative path to a Requirement
       file. May contain unresolved constraints

    .. py:attribute:: _zeroes
       :type: set[FilePins]

       Set of FilePins that have all constraints resolved

    :raises:

       - :py:exc:`TypeError` -- Unsupported type for loader


       - :py:exc:`drain_swamp.exceptions.MissingPackageBaseFolder` --
         loader did not provide package base folder

    """

    loader: VenvMapLoader
    venv_path: dataclasses.InitVar[str]
    _venv_relpath: str = dataclasses.field(init=False)
    _file_pins: list[FilePins] = dataclasses.field(init=False, default_factory=list)
    _iter: Iterator[FilePins] = dataclasses.field(init=False)
    _files: set[FilePins] = dataclasses.field(init=False, default_factory=set)
    _zeroes: set[FilePins] = dataclasses.field(init=False, default_factory=set)

    def __post_init__(
        self,
        venv_path,
    ):
        """Class constructor"""
        check_loader(self.loader)

        """Relative path acts as a dict key. An absolute path is not a key.
        Selecting by always nonexistent key returns empty Sequence, abspath_reqs"""
        dotted_path = f"{g_app_name}.lock_collections.Ins.__init__"
        is_abs_path = is_ok(venv_path) and Path(venv_path).is_absolute()
        is_abspath = (
            venv_path is not None
            and issubclass(type(venv_path), PurePath)
            and venv_path.is_absolute()
        )

        # dataclass will prevent loader from being invalid type
        if is_module_debug:  # pragma: no cover
            msg_info = f"{dotted_path} cwd {self.path_cwd}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        if is_abs_path or is_abspath:
            venv_path = Path(venv_path).relative_to(self.path_cwd).as_posix()
        else:  # pragma: no cover
            pass
        self._venv_relpath = venv_path

    @property
    def path_cwd(self):
        """package base folder. During testing this will be tmp_path,
        not the source package folder

        :returns: package base folder. None is anything else besides a loader
        :rtype: pathlib.Path
        """
        ret = get_path_cwd(self.loader)

        return ret

    def load(self, suffix_last=SUFFIX_IN):
        """Load ``.in`` files

        :raises:

           - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
             missing requirements file(s). Create it

        """
        dotted_path = f"{g_app_name}.lock_collections.Ins.load"
        if suffix_last is None or suffix_last not in ENDINGS:
            suffix_last = SUFFIX_IN
        else:  # pragma: no cover
            pass

        """NotADirectoryError, ValueError, KeyError,
        MissingRequirementsFoldersFiles, MissingPackageBaseFolder"""
        fpins = from_loader_filepins(
            self.loader,
            self._venv_relpath,
            suffix_last=suffix_last,
        )
        self._file_pins = fpins

        # initialize iterator
        self._iter = iter(self._file_pins)

        is_suffix_dot_in = suffix_last == SUFFIX_IN
        if is_suffix_dot_in:
            # move fpins --> _files
            for fpin in fpins:
                self._files.add(fpin)

            if is_module_debug:  # pragma: no cover
                msg_info = f"{dotted_path} _files (before) {self._files}"
                _logger.info(msg_info)
            else:  # pragma: no cover
                pass

            # resolution loop
            try:
                self.resolution_loop()
            except MissingRequirementsFoldersFiles:
                raise

            if is_module_debug:  # pragma: no cover
                msg_info = f"{dotted_path} _files (after) {self._files}"
                _logger.info(msg_info)
            else:  # pragma: no cover
                pass

            if is_module_debug:  # pragma: no cover
                msg_info = f"{dotted_path} _zeroes (after) {self._zeroes}"
                _logger.info(msg_info)
            else:  # pragma: no cover
                pass

        else:  # pragma: no cover
            pass

    def __len__(self):
        """Item count.

        :returns: FilePins count
        :rtype: int
        """
        ret = len(self._file_pins)

        return ret

    def __next__(self):
        """Recreates the iterator every time it's completely consumed

        :returns: One pin within a requirements file
        :rtype: drain_swamp.lock_filepins.FilePins

        .. seealso::

           `reusable_range <https://realpython.com/python-iterators-iterables/#understanding-some-constraints-of-python-iterators>`_

        """
        try:
            return next(self._iter)
        except StopIteration:
            # Reinitialize iterator
            self._iter = iter(self._file_pins)
            # signal end of iteration
            raise

    def __iter__(self):
        """Entire Iterator

        :returns: Iterator
        :rtype: collections.abc.Iterator[typing_extensions.Self[drain_swamp.lock_filepins.FilePins]]
        """
        return self

    def __contains__(self, item):
        """Check if a particular FilePins in Self

        :param item: Item to test if within collection
        :type item: typing.Any
        :returns: True if a FilePins and FilePins in Ins otherwise False
        :rtype: bool
        """
        is_ng = item is None or not isinstance(item, FilePins)
        if is_ng:
            ret = False
        else:
            is_found = False
            for file_pins in self._file_pins:
                # FilePins has no __eq__
                is_same_abspath = file_pins.file_abspath == item.file_abspath
                if is_same_abspath:
                    is_found = True
                else:  # pragma: no cover
                    pass
            ret = is_found

        return ret

    def in_zeroes(self, val):
        """Check if within zeroes

        :param val: item to check if within zeroes
        :type val: typing.Any
        :returns: True if InFile contained within zeroes otherwise False
        :rtype: bool
        """
        ret = in_generic(
            self,
            val,
            "file_abspath",
            set_name=InFileType.ZEROES,
            is_abspath_ok=True,
        )

        return ret

    def in_files(self, val):
        """Check if within InFiles

        :param val: item to check if within InFiles
        :type val: typing.Any
        :returns: True if InFile contained within InFiles otherwise False
        :rtype: bool
        """
        ret = in_generic(
            self,
            val,
            "file_abspath",
            set_name=InFileType.FILES,
            is_abspath_ok=True,
        )

        return ret

    @property
    def files(self):
        """Generator of sorted InFile

        :returns: Yields InFile. These tend to contain constraints
        :rtype: collections.abc.Generator[drain_swamp.lock_infile.InFile, None, None]
        """
        yield from sorted(self._files)

    @files.setter
    def files(self, val):
        """Append an FilePins, requirement or constraint

        :param val:

           :py:class:`~drain_swamp.lock_filepins.FilePins` or absolute path
           to requirement or constraint file

        :type val: typing.Any
        :raises:

           - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
             .in requirements file not found

           - :py:exc:`ValueError` -- file suffixes are not ok

        """
        if val is not None and isinstance(val, FilePins):
            fpin = val
        elif val is not None and issubclass(type(val), PurePath):
            fpin = FilePins(val)
        else:  # pragma: no cover
            fpin = None

        if fpin is not None:
            self._files.add(fpin)
        else:  # pragma: no cover
            pass

    @property
    def files_len(self):
        """Item count within unresolved files set, files

        :returns: files count
        :rtype: int
        """
        ret = len(list(self._files))
        return ret

    @property
    def zeroes(self):
        """Generator of InFile

        :returns: Yields InFile without any constraints
        :rtype: collections.abc.Generator[drain_swamp.lock_infile.InFile, None, None]
        """
        yield from self._zeroes

    @zeroes.setter
    def zeroes(self, val):
        """append an FilePins that doesn't have any constraints

        The only acceptable source of zeroes is from :code:`self._files`

        :param val: Supposed to be an :py:class:`~drain_swamp.lock_filepins.FilePins`
        :type val: typing.Any
        """
        is_infile = val is not None and isinstance(val, FilePins)
        if is_infile:
            self._zeroes.add(val)
        else:  # pragma: no cover
            pass

    @property
    def zeroes_len(self):
        """Item count within resolved files set, zeroes

        :returns: zeroes count
        :rtype: int
        """
        ret = len(list(self._zeroes))

        return ret

    def move_zeroes(self):
        """Zeroes have had all their constraints resolved and therefore
        do not need to be further scrutinized.
        """
        dotted_path = f"{g_app_name}.lock_collections.Ins.move_zeroes"
        # add to self.zeroes
        del_these = []
        for in_ in self.files:
            if in_.depth == 0:
                # set.add an InFile
                self.zeroes = in_
                del_these.append(in_)
            else:  # pragma: no cover
                pass

        if is_module_debug:  # pragma: no cover
            msg_info = f"{dotted_path} self.zeroes (after): {self._zeroes}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        # remove from self._files
        for in_ in del_these:
            self._files.discard(in_)

        if is_module_debug:  # pragma: no cover
            msg_info = f"{dotted_path} self.files (after): {self._files}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

    def resolve_zeroes(self):
        """A requirements (``.in``) file may contain constraints (-c),
        and/or requirements (-r). If possible resolve by a zero
        (a completely resolved file).

        _files and _zeroes are both type, set. When resolved, the FilePins
        instance is moved from _file --> _zeroes

        Constraints vs requirements. What's the difference?

        constraint -- subset of requirements features. Intended to restrict
        package versions. Does not necessarily (might not) install the package

        Does not support:

        - editable mode (-e)

        - extras (e.g. coverage[toml])

        Drain swamp convention

        Requirements files for the purpose as constraints, file name is
        prefixed with ``pins-*[.shared].in``.

        These files do not need to be compiled/rendered into
        ``.lock``/``.unlock`` respectively.

        ``.shared`` means shared across multiple venvs.
        """
        dotted_path = f"{g_app_name}.lock_collections.Ins.resolve_zeroes"

        # Take the win, early and often!
        self.move_zeroes()

        # Add if new constraint?
        abspath_cwd = self.path_cwd

        add_these = []
        # For each file, Process both constraints and requirements
        attrib_and_singular = (
            ("constraints", "constraint"),
            ("requirements", "requirement"),
        )
        for in_ in self.files:
            for plural, singular in attrib_and_singular:
                # Check plural
                is_plural_attrib_exists = is_ok(plural) and hasattr(in_, plural)
                assert is_plural_attrib_exists

                set_plural = getattr(in_, plural)
                for constraint_relpath in set_plural:
                    """relpath is relative to .in file. Want relative
                    to package base folder (cwd)

                    abspath_cwd + relative_relpath_dir + relpath --> resolve
                    """
                    try:
                        abspath_constraint = abspath_relative_to_package_base_folder(
                            abspath_cwd,
                            in_.file_abspath,
                            constraint_relpath,
                        )
                    except FileNotFoundError as exc:
                        msg_warn = (
                            f"{in_.file_abspath} is missing support "
                            f"requirement file {constraint_relpath}"
                        )
                        raise MissingRequirementsFoldersFiles(msg_warn) from exc

                    is_in_zeroes = self.in_zeroes(abspath_constraint)
                    is_in_files = self.in_files(abspath_constraint)
                    is_new = not is_in_zeroes and not is_in_files
                    if is_new:
                        # To add to self._files
                        add_these.append(abspath_constraint)
                    else:  # pragma: no cover
                        pass

        # Add new (contraint|requirement to self.files)
        for abspath_constraint in add_these:
            if is_module_debug:  # pragma: no cover
                msg_info = (
                    f"{dotted_path} abspath_constraint --> self.files "
                    f"setter: {abspath_constraint}"
                )
                _logger.info(msg_info)
            else:  # pragma: no cover
                pass
            self.files = abspath_constraint

        # Any contraints zeroes?
        self.move_zeroes()

        # Resolve with zeroes
        for in_ in self.files:
            for plural, singular in attrib_and_singular:
                set_plural = getattr(in_, plural)
                constaints_copy = copy.deepcopy(set_plural)
                for constraint_relpath in constaints_copy:
                    # may raise FileNotFoundError
                    try:
                        abspath_constraint = abspath_relative_to_package_base_folder(
                            abspath_cwd,
                            in_.file_abspath,
                            constraint_relpath,
                        )
                    except FileNotFoundError as exc:
                        msg_warn = (
                            f"{in_.file_abspath} is missing support "
                            f"requirement file {constraint_relpath}"
                        )
                        raise MissingRequirementsFoldersFiles(msg_warn) from exc
                    is_in_zeroes = self.in_zeroes(abspath_constraint)
                    is_in_files = self.in_files(abspath_constraint)

                    if is_module_debug:  # pragma: no cover
                        msg_info = (
                            f"{dotted_path} {singular!s} {abspath_constraint!r} "
                            f"in zeroes {is_in_zeroes} in files {is_in_files}"
                        )
                        _logger.info(msg_info)
                    else:  # pragma: no cover
                        pass

                    if is_in_zeroes:
                        """Contains constraint|requirement file resolved pins. Without
                        which cannot write a .unlock file
                        Raises ValueError if constraint_relpath is neither str nor Path
                        """
                        item = self.get_by_abspath(
                            abspath_constraint, set_name=InFileType.ZEROES
                        )

                        constraint_relpath_fixed = abspath_constraint.relative_to(
                            self.path_cwd,
                        )

                        if is_module_debug:  # pragma: no cover
                            msg_info = (
                                f"{dotted_path} in_ (before) {in_!r} cwd {self.path_cwd} "
                                f"{singular}_relpath_fixed {constraint_relpath_fixed} "
                                f"{singular}_relpath {constraint_relpath} "
                            )
                            _logger.info(msg_info)
                        else:  # pragma: no cover
                            pass

                        # Provide the unfixed constraint|requirement relative path
                        in_.resolve(
                            constraint_relpath,
                            plural=plural,
                            singular=singular,
                        )

                        """From constraint|requirement, packages are added into
                        parent"""
                        from_child = item._pins
                        from_child_ancestors = item.pkgs_from_resolved
                        in_.packages_save_to_parent(from_child, from_child_ancestors)

                        if is_module_debug:  # pragma: no cover
                            msg_info = f"{dotted_path} in_ (after) {in_!r}"
                            _logger.info(msg_info)
                        else:  # pragma: no cover
                            pass
                    else:  # pragma: no cover
                        pass

        # For an InFile, are all it's constraints resolved?
        self.move_zeroes()

    def get_by_abspath(self, abspath_f, set_name=InFileType.FILES):
        """Get the index and :py:class:`~drain_swamp.lock_filepins.FilePins`

        :param abspath_f: relative path of an ``.in`` file
        :type abspath_f: pathlib.Path
        :param set_name:

           Default :py:attr:`drain_swamp.lock_datum.InFileType.FILES`.
           Which set to search thru. zeroes or files.

        :type set_name: str | None
        :returns:

           The ``.in`` file and index within
           :py:class:`~drain_swamp.lock_filepins.FilePins`

        :rtype: drain_swamp.lock_filepins.FilePins | None
        :raises:

            - :py:exc:`ValueError` -- Unsupported type. relpath is neither str nor Path

        """
        file_name = "file_abspath"
        if set_name is None or not isinstance(set_name, InFileType):
            str_set_name = str(InFileType.FILES)
        else:  # pragma: no cover
            str_set_name = str(set_name)

        msg_exc = f"Expected an absolute Path. Got {type(abspath_f)}"
        if abspath_f is not None:
            if issubclass(type(abspath_f), PurePath):
                abspath_g = abspath_f
            else:
                raise ValueError(msg_exc)
        else:
            raise ValueError(msg_exc)

        ret = None
        set_ = getattr(self, str_set_name, set())
        for in_ in set_:
            if getattr(in_, file_name) == abspath_g:
                ret = in_
                break
            else:  # pragma: no cover
                # not a match
                pass
        else:
            # set empty
            ret = None

        return ret

    def resolution_loop(self):
        """Run loop of resolve_zeroes calls, sampling before and after
        counts. If not fully resolved and two iterations have the same
        result, raise an Exception

        :raises:

           - :py:exc:`drain_swamp.exceptions.MissingRequirementsFoldersFiles` --
             there are unresolvable constraint(s)

        """
        dotted_path = f"{g_app_name}.lock_collections.Ins.resolution_loop"
        initial_count_files = self.files_len
        initial_count_zeroes = self.zeroes_len
        current_count_files = initial_count_files
        previous_count_files = initial_count_files
        current_count_zeroes = initial_count_zeroes
        previous_count_zeroes = initial_count_zeroes
        while current_count_files != 0:
            if is_module_debug:  # pragma: no cover
                msg_info = (
                    f"{dotted_path} (before resolve_zeroes) resolution current "
                    f"state. previous_count files {previous_count_files} "
                    f"current count files {current_count_files} "
                    f"previous count zeroes {previous_count_zeroes} "
                    f"current count zeroes {current_count_zeroes} "
                    f"files {self._files}\n"
                    f"zeroes {self._zeroes}"
                )
                _logger.info(msg_info)
            else:  # pragma: no cover
                pass

            self.resolve_zeroes()

            current_count_files = self.files_len
            current_count_zeroes = self.zeroes_len
            # Check previous run results vs current run results, if same raise Exception
            is_resolved = current_count_files == 0
            is_result_same_files = previous_count_files == current_count_files
            is_result_same_zeroes = previous_count_zeroes == current_count_zeroes

            if is_module_debug:  # pragma: no cover
                msg_info = (
                    f"{dotted_path} (after resolve_zeroes) "
                    "resolution current state. current count files "
                    f"{current_count_files} "
                    f"current count zeroes {current_count_zeroes} "
                    f"files {self._files}\n"
                    f"zeroes {self._zeroes}"
                )
                _logger.info(msg_info)
            else:  # pragma: no cover
                pass

            # raise exception if not making any progress
            is_result_same = is_result_same_files and is_result_same_zeroes
            if not is_resolved and is_result_same:
                remaining_files = [in_.file_abspath for in_ in self.files]
                missing_contraints = [in_.constraints for in_ in self.files]
                missing_requirements = [in_.requirements for in_ in self.files]
                msg_warn = (
                    f"{dotted_path} Missing .in requirements file(s). "
                    "Unable to resolve constraint(s) or requirements(s). "
                    f"Files remaining: {remaining_files}. "
                    f"Missing constraints (-c): {missing_contraints} "
                    f"Missing requirements (-r): {missing_requirements}"
                )
                _logger.warning(msg_warn)
                raise MissingRequirementsFoldersFiles(msg_warn)
            else:  # pragma: no cover
                pass

            previous_count_files = current_count_files
            previous_count_zeroes = current_count_zeroes

    def write(self):
        """After resolving all constraints. Write out all .unlock files

        :returns: Generator of ``.unlock`` absolute paths
        :rtype: collections.abc.Generator[pathlib.Path, None, None]

        .. code-block:: shell

           pipenv-unlock unlock --path=[test folder] --venv-relpath='.venv'

        """
        dotted_path = f"{g_app_name}.lock_collections.Ins.write"
        if is_module_debug:  # pragma: no cover
            msg_info = f"{dotted_path} zeroes count: {self.zeroes_len}"
            _logger.info(msg_info)
        else:  # pragma: no cover
            pass

        for in_ in self.zeroes:
            abspath_zero = in_.file_abspath
            is_shared_pin = abspath_zero.name.startswith("pins") and is_shared(
                abspath_zero.name
            )
            if not is_shared_pin:
                abspath_unlocked = replace_suffixes_last(
                    abspath_zero,
                    SUFFIX_UNLOCKED,
                )

                # in_._pins lacks constraints and requirements
                sep = os.linesep
                lst_reqs_unsorted = []
                for pindatum in in_._pins:
                    lst_reqs_unsorted.append(pindatum.line)

                # From children
                for package_line in in_.pkgs_from_resolved:
                    lst_reqs_unsorted.append(package_line)

                # reqs --> sorted --> file contents
                lst_reqs_alphabetical = sorted(lst_reqs_unsorted)
                contents = sep.join(lst_reqs_alphabetical)
                is_has_contents = len(contents.strip()) != 0
                if is_has_contents:
                    contents = f"{contents}{sep}"

                    if is_module_debug:  # pragma: no cover
                        msg_info = (
                            f"{dotted_path} abspath_unlocked: {abspath_unlocked}"
                            f"{sep}{contents}"
                        )
                        _logger.info(msg_info)
                    else:  # pragma: no cover
                        pass

                    is_file = abspath_unlocked.exists() and abspath_unlocked.is_file()
                    if not is_file:
                        abspath_unlocked.touch(mode=0o644, exist_ok=True)
                    else:  # pragma: no cover
                        pass

                    is_file = abspath_unlocked.exists() and abspath_unlocked.is_file()
                    if is_module_debug:  # pragma: no cover
                        msg_info = f"{dotted_path} is_file: {is_file}"
                        _logger.info(msg_info)
                    else:  # pragma: no cover
                        pass

                    if is_file:
                        abspath_unlocked.write_text(contents)
                        yield abspath_unlocked
                    else:  # pragma: no cover
                        pass
                else:  # pragma: no cover
                    pass
            else:  # pragma: no cover
                pass

        yield from ()


def unlock_compile(loader, venv_relpath):
    """Create .unlock files

    :param loader: Contains some paths and loaded unparsed mappings
    :type loader: drain_swamp.pep518_venvs.VenvMapLoader
    :param venv_relpath: venv relative path is a key. To choose a tools.venvs.req
    :type venv_relpath: typing.Any | None
    :returns: Generator of abs path to .unlock files
    :rtype: collections.abc.Generator[pathlib.Path, None, None]
    """
    if is_ok(venv_relpath):
        ins = Ins(loader, venv_relpath)
        ins.load()
        gen = ins.write()
        lst_called = list(gen)
        for abspath in lst_called:
            assert abspath.exists() and abspath.is_file()

        yield from lst_called
    else:
        msg_warn = (
            "One venv at a time, creating .unlock files with same python "
            "interpreter! Do all venvs require the same Python "
            "interpreter version?! If not, the results will be wrong"
        )
        _logger.warning(msg_warn)
        for venv_path in loader.venv_relpaths:
            ins = Ins(loader, venv_path)
            ins.load()
            gen = ins.write()
            lst_called = list(gen)
            for abspath in lst_called:
                assert abspath.exists() and abspath.is_file()

        yield from lst_called

    yield from ()
