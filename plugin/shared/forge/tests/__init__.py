"""Tests for the portable Forge workflow utilities."""

import unittest

from . import test_run_static_evals


def load_tests(loader, _tests, _pattern):
    """Load Forge's shared test module for ``python -m unittest ...tests``."""
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(test_run_static_evals))
    return suite
