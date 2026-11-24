"""Tests for pull_gsw, on a synthetic file in the Fed's format. No network."""

import numpy as np
import pandas as pd
import pytest

from pull_gsw import KEEP_COLS, filter_sample, parse_gsw_csv


def make_fed_csv(rows, extra_cols=("SVENF01", "SVENPY01")):
    """Build a synthetic ``feds200628.csv``: preamble, header, then ``rows``.

    ``rows`` maps a date string to a value used for every column, or None for a
    holiday row of all ``NA``. Extra columns check that only KEEP_COLS are kept.
    """
    cols = list(extra_cols) + KEEP_COLS
    preamble = [
        '"Note: This is not an official Federal Reserve statistical release."',
        "",
        "Series,Compounding Convention,Mnemonic(s)",
        "Zero-coupon yield,Continuously Compounded,SVENYXX",
        "Parameters,N/A,BETA0 to TAU2",
        "",
    ]
    body = ["Date," + ",".join(cols)]
    for date, value in rows.items():
        cell = "NA" if value is None else str(value)
        body.append(date + "," + ",".join([cell] * len(cols)))
    return "\n".join(preamble + body) + "\n"


def test_parse_finds_header_and_keeps_columns():
    df = parse_gsw_csv(make_fed_csv({"2004-01-02": 1.5, "2004-01-05": 2.5}))
    assert list(df.columns) == ["date", *KEEP_COLS]
    assert len(df) == 2
    assert df["date"].dtype == "datetime64[ns]"
    assert df.loc[1, "SVENY10"] == 2.5  # still in percent: no conversion here


def test_parse_reads_na_as_missing():
    df = parse_gsw_csv(make_fed_csv({"2004-01-01": None, "2004-01-02": 1.0}))
    assert df.loc[0, KEEP_COLS].isna().all()
    assert not df.loc[1, KEEP_COLS].isna().any()


def test_parse_sorts_by_date():
    df = parse_gsw_csv(make_fed_csv({"2004-01-05": 2.0, "2004-01-02": 1.0}))
    assert df["date"].is_monotonic_increasing


def test_parse_raises_without_header():
    with pytest.raises(ValueError, match="header"):
        parse_gsw_csv("just,a,preamble\n1,2,3\n")


def test_parse_raises_on_missing_column():
    text = make_fed_csv({"2004-01-02": 1.0}).replace("TAU2", "TAUX")
    with pytest.raises(ValueError, match="TAU2"):
        parse_gsw_csv(text)


def test_filter_sample_is_inclusive_and_drops_holidays():
    df = parse_gsw_csv(
        make_fed_csv(
            {
                "2003-12-31": 1.0,  # before the sample
                "2004-01-01": None,  # holiday: all NA
                "2004-01-02": 2.0,  # first day, inclusive
                "2004-01-05": 3.0,  # last day, inclusive
                "2004-01-06": 4.0,  # after the sample
            }
        )
    )
    out = filter_sample(df, start="2004-01-01", end="2004-01-05")
    assert list(out["date"]) == [pd.Timestamp("2004-01-02"), pd.Timestamp("2004-01-05")]


def test_filter_sample_keeps_partly_missing_rows():
    """A row with some values missing is real data: only all-NA rows go."""
    df = parse_gsw_csv(make_fed_csv({"2004-01-02": 1.0}))
    df.loc[0, "SVENY30"] = np.nan
    out = filter_sample(df, start="2004-01-01", end="2004-12-31")
    assert len(out) == 1
