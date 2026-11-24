"""Tests for the committed constants in settings.py.

The constants decide what a commit computes, so neither .env, the environment
nor the command line may change them. These tests need no data or credentials.
"""

from datetime import date

import pytest

import settings
from settings import COMMITTED_CONSTANTS, config


@pytest.mark.parametrize("name", COMMITTED_CONSTANTS)
def test_config_refuses_committed_constants(name):
    """Each committed constant exists, and config() raises instead of reading it."""
    assert hasattr(settings, name)
    with pytest.raises(ValueError, match="committed constant"):
        config(name)


def test_env_override_raises(monkeypatch):
    """A committed constant set in the environment (or .env) raises an error."""
    monkeypatch.setenv("END_DATE", "2030-01-01")
    with pytest.raises(ValueError, match="END_DATE"):
        settings.check_no_overrides(cli_vars={})


def test_cli_override_raises():
    """A committed constant passed as --END_DATE=... raises too."""
    with pytest.raises(ValueError, match="END_DATE"):
        settings.check_no_overrides(cli_vars={"END_DATE": "2030-01-01"})


def test_no_overrides_by_default():
    """With nothing set, the check passes."""
    settings.check_no_overrides(cli_vars={})


def test_sample_dates_are_ordered_iso_dates():
    """The dates parse as ISO dates, and START_DATE < REPLICATION_END <= END_DATE."""
    start, replication_end, end = (
        date.fromisoformat(d)
        for d in (settings.START_DATE, settings.REPLICATION_END, settings.END_DATE)
    )
    assert start < replication_end <= end


def test_tenors_are_increasing_whole_months():
    """The tenors are positive whole months, increasing, with no duplicates."""
    tenors = settings.TENORS_M
    assert all(isinstance(m, int) and m > 0 for m in tenors)
    assert list(tenors) == sorted(set(tenors))


def test_config_returns_local_default():
    """An unset variable with a local default returns it (cast or not)."""
    assert config("P18_TEST_UNSET_VAR", default="abc") == "abc"
    assert config("P18_TEST_UNSET_VAR", default="3", cast=int) == 3


def test_config_raises_without_default():
    """An unset variable without a default raises a clear error."""
    with pytest.raises(ValueError, match="is not defined"):
        config("P18_TEST_UNSET_VAR")
