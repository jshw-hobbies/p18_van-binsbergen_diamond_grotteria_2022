"""Tests for pull_fred, on synthetic fredgraph CSVs. No network."""

import numpy as np
import pandas as pd
import pytest

from pull_fred import combine_series, parse_fred_csv


def fred_csv(series_id, rows):
    """A synthetic fredgraph CSV; a value of None is written as FRED's '.'."""
    lines = [f"observation_date,{series_id}"]
    lines += [f"{d},{'.' if v is None else v}" for d, v in rows.items()]
    return "\n".join(lines) + "\n"


def test_parse_reads_dot_as_missing():
    s = parse_fred_csv(
        fred_csv("DTB3", {"2004-01-01": None, "2004-01-02": 0.9}), "DTB3"
    )
    assert np.isnan(s.loc["2004-01-01"])
    assert s.loc["2004-01-02"] == 0.9  # still in percent: no conversion here
    assert s.dtype == float


def test_parse_raises_on_html_page():
    with pytest.raises(ValueError, match="BGCR"):
        parse_fred_csv("<html lang='en'>\n<body>Not found</body></html>\n", "BGCR")


def test_combine_outer_joins_and_drops_all_missing_dates():
    a = parse_fred_csv(fred_csv("DTB3", {"2018-04-02": 1.7, "2018-04-03": 1.8}), "DTB3")
    b = parse_fred_csv(
        fred_csv("SOFR", {"2018-04-03": 1.83, "2018-04-04": None}), "SOFR"
    )
    df = combine_series({"DTB3": a, "SOFR": b})
    assert list(df.columns) == ["date", "DTB3", "SOFR"]
    assert list(df["date"]) == [pd.Timestamp("2018-04-02"), pd.Timestamp("2018-04-03")]
    assert np.isnan(df.loc[0, "SOFR"])  # SOFR starts later: kept as NaN
