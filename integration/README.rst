integration/test_pep366.py will disrupt coverage.

Entrypoints are:

- run from source code

- uses importlib, modifies the sys.path, and sets __spec__

Integration tests **do not** contribute to coverage. Isolated, not due
to slow execution, cuz does not play nice with coverage
