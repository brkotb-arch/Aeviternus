"""
Runtime validation tests.
"""

import sys


def test_python_version():
    assert sys.version_info >= (3, 11)


def test_project_name():
    name = "Aeviternus"

    assert name == "Aeviternus"