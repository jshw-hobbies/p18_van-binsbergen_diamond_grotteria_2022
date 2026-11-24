"""Download the Gurkaynak, Sack and Wright (2007) Treasury yield curve from the Fed.

Domain B (benchmark rates). Stage: pull.

Source
------
The Federal Reserve's ``feds200628.csv``: daily, free, no credentials.

Output
------
``DATA_DIR/gsw_yield_curve.parquet``, raw, one row per date from ``START_DATE``
to ``END_DATE`` (inclusive):

- ``date``;
- the zero-coupon yields ``SVENY01`` to ``SVENY30``: continuously compounded, in
  percent, at annual maturities only;
- the Svensson parameters ``BETA0`` to ``BETA3`` (in percent) and ``TAU1``,
  ``TAU2`` (in years), from which ``calc_benchmarks`` computes the 3-, 6- and
  18-month yields.

Values stay in the Fed's units: ``calc_benchmarks`` converts them to decimals.
The only rows dropped are dates on which every kept column is missing (the Fed
file lists market holidays, such as 2004-01-01, with all values ``NA``).

Reuse: the course's ``fed_yield_curve`` repo, ``src/pull_fed_yield_curve.py``
(the download, as in HW2 ``src/pull_yield_curve_data.py``). That code skips a
fixed 9 preamble lines; here the header row is found by its ``Date,`` prefix, so
a change to the Fed's preamble cannot shift the columns.
"""

from io import StringIO
from pathlib import Path

import pandas as pd
import requests

from settings import END_DATE, START_DATE, config

DATA_DIR = config("DATA_DIR")
OUTPUT_FILE = "gsw_yield_curve.parquet"

URL = "https://www.federalreserve.gov/data/yield-curve-tables/feds200628.csv"

SVENY_COLS = [f"SVENY{n:02d}" for n in range(1, 31)]
PARAM_COLS = ["BETA0", "BETA1", "BETA2", "BETA3", "TAU1", "TAU2"]
KEEP_COLS = SVENY_COLS + PARAM_COLS


def parse_gsw_csv(text):
    """Parse the text of ``feds200628.csv`` into a DataFrame with a ``date`` column.

    The file opens with a free-text preamble (a disclaimer and a table of series
    names), then a header row starting with ``Date,``. Missing values are
    ``NA``. Keeps ``date`` and ``KEEP_COLS``; raises if any of them is absent.
    """
    lines = text.splitlines()
    try:
        header = next(i for i, line in enumerate(lines) if line.startswith("Date,"))
    except StopIteration:
        raise ValueError("No header row starting with 'Date,' in the GSW file")

    df = pd.read_csv(StringIO("\n".join(lines[header:])), na_values=["NA"])
    missing = [c for c in KEEP_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"GSW file is missing columns: {missing}")

    df = df.rename(columns={"Date": "date"})
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    return df[["date", *KEEP_COLS]].sort_values("date").reset_index(drop=True)


def filter_sample(df, start=START_DATE, end=END_DATE):
    """Keep dates from ``start`` to ``end`` (inclusive), and drop all-missing rows.

    All-missing rows are market holidays that the Fed lists without values.
    """
    in_sample = df["date"].between(pd.Timestamp(start), pd.Timestamp(end))
    out = df.loc[in_sample]
    rows_in = len(out)
    out = out.dropna(how="all", subset=KEEP_COLS).reset_index(drop=True)
    print(f"GSW: {rows_in} -> {len(out)} rows (dropped all-missing dates)")
    return out


def pull_gsw(url=URL, start=START_DATE, end=END_DATE):
    """Download the GSW file and return the sample period's rows, in the Fed's units."""
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    return filter_sample(parse_gsw_csv(response.text), start=start, end=end)


def load_gsw(data_dir=DATA_DIR):
    """Load ``gsw_yield_curve.parquet`` from ``data_dir``."""
    return pd.read_parquet(Path(data_dir) / OUTPUT_FILE)


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = pull_gsw()
    df.to_parquet(DATA_DIR / OUTPUT_FILE, index=False)
    print(
        f"GSW: wrote {len(df)} rows, {df['date'].min():%Y-%m-%d} to "
        f"{df['date'].max():%Y-%m-%d}, to {DATA_DIR / OUTPUT_FILE}"
    )
