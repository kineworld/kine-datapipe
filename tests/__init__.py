"""Make every ``test_*`` function in this package visible to the standard runner.

``tests/test_windows.py`` is written to be run directly (``python tests/test_windows.py``)
rather than as a ``unittest.TestCase`` subclass, so ``unittest discover`` collected
**nothing at all**:

    $ python -m unittest discover -s tests
    Ran 0 tests in 0.000s
    NO TESTS RAN

The file was never broken. The loader simply cannot see bare functions, and with no CI
there was nothing to notice. This module implements the documented ``load_tests``
protocol so the four tests are collected, without rewriting them.

Use either of:

    python -m unittest discover -s tests -t .
    python -m unittest tests

``-t .`` matters: without it, ``discover`` treats ``tests/`` as a directory of top-level
modules, never imports this package, and ``load_tests`` would never run. The same rule is
applied by ``tests/check_collection.py`` and by
``kineworld/.github/.github/workflows/python-tests.yml``, so the guard and the run cannot
disagree about what "collected" means.

Note that a ``load_tests`` function *replaces* the default collection for this package
rather than adding to it. That is why this loads ``TestCase`` classes as well as wrapping
bare functions: the same file in kineworld/kine-jepa#4 collected only the bare functions
at first, which would have silently dropped five test methods from two other files.
"""

import importlib
import inspect
import pkgutil
import unittest


def _wrap(module_name, function_name, function):
    """Return a TestCase that runs one bare ``test_*`` function."""

    class _BareFunctionTest(unittest.TestCase):
        def runTest(self):  # noqa: N802 - unittest's own protocol name
            function()

    _BareFunctionTest.__name__ = "Test_%s_%s" % (module_name, function_name)
    _BareFunctionTest.__qualname__ = _BareFunctionTest.__name__
    return _BareFunctionTest()


def _modules():
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda i: i.name):
        if info.name.startswith("test_"):
            yield info.name, importlib.import_module("%s.%s" % (__name__, info.name))


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for module_name, module in _modules():
        # 1. TestCase subclasses declared in the module, via the standard loader.
        suite.addTests(loader.loadTestsFromModule(module))
        # 2. Bare test_* functions, which that loader ignores.
        for name, obj in sorted(vars(module).items()):
            if name.startswith("test_") and inspect.isfunction(obj):
                suite.addTest(_wrap(module_name, name, obj))
    return suite
