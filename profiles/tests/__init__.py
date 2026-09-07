"""Profile app test modules."""

import pathlib
import unittest


def load_tests(loader, tests, pattern):
    """Include ``*_tests.py`` modules that the default ``test*.py`` pattern skips.

    Module names here (e.g. ``organization_tests``) do not start with ``test``,
    so unittest's default discovery would ignore them. Loading the package
    invokes this hook instead and each ``*_tests.py`` module is added to the
    suite explicitly.
    """
    test_dir = pathlib.Path(__file__).parent
    suite = unittest.TestSuite()
    for path in sorted(test_dir.glob("*_tests.py")):
        suite.addTests(loader.loadTestsFromName(f"profiles.tests.{path.stem}"))
    return suite
