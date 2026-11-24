"""Pull benchmark rate series from FRED.

Domain B (benchmark rates). Stage: pull.

Series
------
Pulled through FRED's public CSV download (no API key):

========== ============================================ ======================
Code       Series                                       Quoted as
========== ============================================ ======================
SOFR       Secured Overnight Financing Rate (2018-04 on) percent, simple, ACT/360
EFFR       Effective federal funds rate                 percent, simple, ACT/360
DTB4WK     4-week T-bill, secondary market              percent, discount basis
DTB3       3-month T-bill, secondary market             percent, discount basis
DTB6       6-month T-bill, secondary market             percent, discount basis
DTB1YR     52-week T-bill (2008-06 on)                  percent, discount basis
DGS1MO     1-month constant-maturity Treasury           percent, bond-equivalent
DGS3MO     3-month constant-maturity Treasury           percent, bond-equivalent
DGS6MO     6-month constant-maturity Treasury           percent, bond-equivalent
DGS1       1-year constant-maturity Treasury            percent, bond-equivalent
DGS2       2-year constant-maturity Treasury            percent, bond-equivalent
DGS3       3-year constant-maturity Treasury            percent, bond-equivalent
========== ============================================ ======================

The T-bills give the ``tbill`` benchmark; the constant-maturity yields
cross-check GSW; SOFR is the update's overnight benchmark after LIBOR.

Not on FRED (checked 2026-11-23), so they come from Bloomberg in
``DATA_DIR/manual/``, or are left out:

- **OIS**: no series.
- **GC repo**: FRED has no term GC repo rate. BGCR and TGCR are not on FRED
  (the New York Fed publishes them), and they are overnight rates, so they
  cannot stand in for the paper's 3-month GC repo rate in Table 2.
- **LIBOR**: ICE's LIBOR series were removed from FRED in 2022. The pipeline
  uses OptionMetrics ``zerocd`` (``pull_zerocd``) as its LIBOR-implied curve.

Output
------
``DATA_DIR/fred.parquet``: a ``date`` column and one column per series, named by
its FRED code, raw, in the units FRED publishes (percent). Dates from
``START_DATE`` to ``END_DATE``. ``calc_benchmarks`` converts the units.

Reuse: the midterm report's ``src/pull_fred.py`` (``pull_series``,
``pull_fred``), without its exhibit registry: the series list is fixed here.
"""

import io
import time
from pathlib import Path

import pandas as pd
import requests

from settings import END_DATE, START_DATE, config

DATA_DIR = config("DATA_DIR")
OUTPUT_FILE = "fred.parquet"

FREDGRAPH_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

SERIES = [
    "SOFR",
    "EFFR",
    "DTB4WK",
    "DTB3",
    "DTB6",
    "DTB1YR",
    "DGS1MO",
    "DGS3MO",
    "DGS6MO",
    "DGS1",
    "DGS2",
    "DGS3",
]


def parse_fred_csv(text, series_id):
    """Parse one fredgraph CSV into a float Series indexed by date.

    FRED writes missing observations (holidays) as ``.``; they become NaN.
    Raises if the response is not the expected CSV (FRED returns an HTML page
    for an unknown series).
    """
    df = pd.read_csv(io.StringIO(text), na_values=".")
    if series_id not in df.columns:
        raise ValueError(f"FRED response for {series_id} has no {series_id} column")
    date_col = df.columns[0]  # "observation_date"
    df[date_col] = pd.to_datetime(df[date_col], format="%Y-%m-%d")
    return df.set_index(date_col)[series_id].astype(float)


def pull_series(series_id, start=START_DATE, end=END_DATE, timeout=60):
    """Download one FRED series, from ``start`` to ``end``, in FRED's units."""
    params = {"id": series_id, "cosd": start, "coed": end}
    response = requests.get(FREDGRAPH_URL, params=params, timeout=timeout)
    response.raise_for_status()
    return parse_fred_csv(response.text, series_id)


def combine_series(columns):
    """Outer-join a dict of {code: Series} on date into a frame with a ``date`` column.

    Drops dates on which every series is missing (holidays common to all).
    """
    df = pd.DataFrame(columns).sort_index()
    df.index.name = "date"
    return df.dropna(how="all").reset_index()


def pull_fred(series=SERIES, start=START_DATE, end=END_DATE, pause=0.5):
    """Download every series in ``series`` and combine them on date."""
    columns = {}
    for series_id in series:
        columns[series_id] = pull_series(series_id, start, end)
        time.sleep(pause)  # be polite to FRED
    return combine_series(columns)


def load_fred(data_dir=DATA_DIR):
    """Load ``fred.parquet`` from ``data_dir``."""
    return pd.read_parquet(Path(data_dir) / OUTPUT_FILE)


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = pull_fred()
    df.to_parquet(DATA_DIR / OUTPUT_FILE, index=False)
    print(
        f"FRED: wrote {len(df)} rows x {len(SERIES)} series to {DATA_DIR / OUTPUT_FILE}"
    )
