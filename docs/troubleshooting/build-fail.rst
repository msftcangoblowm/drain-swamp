Build fails
============

Assumptions
------------

- :code:`validate-pyproject pyproject.toml` ... works

- :code:`pip list | grep drain-swamp` ... not installed

- :code:`python -c "import build.util; print(build.util.project_wheel_metadata('.').get('Requires-Dist'))"` ... fails

- :code:`python src/pipenv_unlock/cli_igor.py build --kind="0.0.1"` ... fails

.. code-block:: shell

   pip-compile pyproject.toml

.. code-block:: text

   Backend subprocess exited when trying to invoke get_requires_for_build_wheel
   Failed to parse /home/faulkmore/Downloads/git_decimals/pipenv_unlock/pyproject.toml

To see the verbose error message

.. code-block:: shell

   python -m build

.. code-block:: text

   * Creating isolated environment: venv+pip...
   * Installing packages in isolated environment:
     - build
     - setuptools>=70.0.0
     - setuptools_scm>=8
     - wheel
   * Getting build dependencies for sdist...
   WARNING setuptools_scm.run_cmd branch err (abbrev-err) CompletedProcess(args=['git', '--git-dir', '/home/faulkmore/Downloads/git_decimals/pipenv_unlock/.git', 'rev-parse', '--abbrev-ref', 'HEAD'], returncode=128, stdout='HEAD', stderr="fatal: ambiguous argument 'HEAD': unknown revision or path not in the working tree.\nUse '--' to separate paths from revisions, like this:\n'git <command> [<revision>...] -- [<file>...]'")
   WARNING setuptools_scm.run_cmd logging the iso date for head failed CompletedProcess(args=['git', '--git-dir', '/home/faulkmore/Downloads/git_decimals/pipenv_unlock/.git', '-c', 'log.showSignature=false', 'log', '-n', '1', 'HEAD', '--format=%cI'], returncode=128, stdout='', stderr="fatal: ambiguous argument 'HEAD': unknown revision or path not in the working tree.\nUse '--' to separate paths from revisions, like this:\n'git <command> [<revision>...] -- [<file>...]'")
   Traceback (most recent call last):
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/_vendor/packaging/requirements.py", line 35, in __init__
       parsed = _parse_requirement(requirement_string)
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/_vendor/packaging/_parser.py", line 64, in parse_requirement
       return _parse_requirement(Tokenizer(source, rules=DEFAULT_RULES))
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/_vendor/packaging/_parser.py", line 73, in _parse_requirement
       name_token = tokenizer.expect(
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/_vendor/packaging/_tokenizer.py", line 140, in expect
       raise self.raise_syntax_error(f"Expected {expected}")
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/_vendor/packaging/_tokenizer.py", line 165, in raise_syntax_error
       raise ParserSyntaxError(
   setuptools.extern.packaging._tokenizer.ParserSyntaxError: Expected package name at the start of dependency specifier
       -c pip.in
       ^

   The above exception was the direct cause of the following exception:

   Traceback (most recent call last):
     File "/home/faulkmore/Downloads/git_decimals/pipenv_unlock/.venv/lib/python3.9/site-packages/pyproject_hooks/_in_process/_in_process.py", line 373, in <module>
       main()
     File "/home/faulkmore/Downloads/git_decimals/pipenv_unlock/.venv/lib/python3.9/site-packages/pyproject_hooks/_in_process/_in_process.py", line 357, in main
       json_out["return_val"] = hook(**hook_input["kwargs"])
     File "/home/faulkmore/Downloads/git_decimals/pipenv_unlock/.venv/lib/python3.9/site-packages/pyproject_hooks/_in_process/_in_process.py", line 308, in get_requires_for_build_sdist
       return hook(config_settings)
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/build_meta.py", line 328, in get_requires_for_build_sdist
       return self._get_build_requires(config_settings, requirements=[])
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/build_meta.py", line 295, in _get_build_requires
       self.run_setup()
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/build_meta.py", line 311, in run_setup
       exec(code, locals())
     File "<string>", line 69, in <module>
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/__init__.py", line 103, in setup
       return distutils.core.setup(**attrs)
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/_distutils/core.py", line 158, in setup
       dist.parse_config_files()
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/dist.py", line 632, in parse_config_files
       pyprojecttoml.apply_configuration(self, filename, ignore_option_errors)
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/config/pyprojecttoml.py", line 69, in apply_configuration
       return _apply(dist, config, filepath)
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/config/_apply_pyprojecttoml.py", line 63, in apply
       dist._finalize_requires()
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/dist.py", line 368, in _finalize_requires
       self._normalize_requires()
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/dist.py", line 384, in _normalize_requires
       self.extras_require = {
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/dist.py", line 385, in <dictcomp>
       k: list(map(str, _reqs.parse(v or []))) for k, v in extras_require.items()
     File "/tmp/build-env-z2ppyvw_/lib/python3.9/site-packages/setuptools/_vendor/packaging/requirements.py", line 37, in __init__
       raise InvalidRequirement(str(e)) from e
   setuptools.extern.packaging.requirements.InvalidRequirement: Expected package name at the start of dependency specifier
       -c pip.in
       ^

   ERROR Backend subprocess exited when trying to invoke get_requires_for_build_sdist

``-c %.in`` is a constraint lines. Which is ``pip-tools`` syntax.

:code:`python -m build` does not understand ``pip-tools`` syntax.

``.unlock`` and ``.lock`` are *compiled*, resolving/removing the constraint
lines. This both ``build`` and ``pip`` can understand

.. seealso::

   https://pypi.org/project/pip-requirements-parser/
