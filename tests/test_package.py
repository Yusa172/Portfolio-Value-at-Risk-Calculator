"""Smoke tests for the installed ``var_calculator`` package."""

import re
from importlib.metadata import version

import var_calculator


def test_package_exposes_version() -> None:
    assert isinstance(var_calculator.__version__, str)
    assert re.fullmatch(r"\d+\.\d+\.\d+", var_calculator.__version__)


def test_version_matches_installed_metadata() -> None:
    assert version("var-calculator") == var_calculator.__version__


def test_public_api_lists_version() -> None:
    assert "__version__" in var_calculator.__all__
