"""Tests for pull_zerocd.

The SQL runs against an in-memory SQLite database holding a synthetic
``optionm_all.zerocd`` table, so these need no credentials. The one test that
connects to WRDS is marked ``wrds`` and is skipped unless run with
``uv run pytest -m wrds`` (one Duo push).
"""

import sqlite3

import pandas as pd
import pytest

from pull_zerocd import _iso_date, tidy_zerocd, zerocd_query


@pytest.fixture
def sqlite_zerocd():
    """An in-memory database with a synthetic ``optionm_all.zerocd`` table."""
    con = sqlite3.connect(":memory:")
    con.execute("ATTACH DATABASE ':memory:' AS optionm_all")
    con.execute("CREATE TABLE optionm_all.zerocd (date TEXT, days INT, rate REAL)")
    rows = [
        ("2003-12-31", 30, 1.10),  # before the sample
        ("2004-01-02", 90, 1.20),
        ("2004-01-02", 30, 1.15),
        ("2004-01-05", 30, 1.16),
        ("2004-01-06", 30, 1.17),  # after the sample
    ]
    con.executemany("INSERT INTO optionm_all.zerocd VALUES (?, ?, ?)", rows)
    yield con
    con.close()


def test_query_filters_dates_inclusively_and_sorts(sqlite_zerocd):
    sql = zerocd_query("2004-01-02", "2004-01-05")
    df = tidy_zerocd(pd.read_sql_query(sql, sqlite_zerocd))
    assert list(df["date"].dt.strftime("%Y-%m-%d")) == [
        "2004-01-02",
        "2004-01-02",
        "2004-01-05",
    ]
    assert list(df["days"]) == [30, 90, 30]  # sorted by date, then days


def test_tidy_keeps_units_and_types(sqlite_zerocd):
    df = tidy_zerocd(pd.read_sql_query(zerocd_query(), sqlite_zerocd))
    assert list(df.columns) == ["date", "days", "rate"]
    assert df["date"].dtype == "datetime64[ns]"
    assert df["days"].dtype == "int64"
    assert df.loc[0, "rate"] == 1.15  # still in percent: no conversion here


def test_iso_date_rejects_non_dates():
    assert _iso_date("2004-01-02") == "2004-01-02"
    with pytest.raises(ValueError):
        _iso_date("2004-01-02'; DROP TABLE zerocd; --")


@pytest.mark.wrds
def test_zerocd_on_wrds():
    """One short query on WRDS: a week of zerocd has rows in percent."""
    from pull_zerocd import connect_wrds, pull_zerocd

    db = connect_wrds()
    try:
        df = pull_zerocd(db, "2004-01-02", "2004-01-09")
    finally:
        db.close()
    assert len(df) > 0
    assert df["rate"].between(0.5, 5.0).all()  # early 2004: 1 to 3 percent
