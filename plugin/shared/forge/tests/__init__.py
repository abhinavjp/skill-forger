"""Tests for the portable Forge workflow utilities."""

import unittest

from . import test_run_static_evals, test_workflow_state


def load_tests(loader, _tests, _pattern):
    """Load Forge's two test modules for ``python -m unittest ...tests``."""
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(test_run_static_evals))
    suite.addTests(loader.loadTestsFromModule(test_workflow_state))
    return suite
