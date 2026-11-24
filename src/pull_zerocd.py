"""Pull the OptionMetrics zero-coupon yield curve (``optionm_all.zerocd``) from WRDS.

Domain B (benchmark rates). Stage: pull.

Output
------
``DATA_DIR/optionm_zerocd.parquet``: ``date, days, rate``, raw, one row per date
and maturity, from ``START_DATE`` to ``END_DATE``. ``days`` is calendar days to
maturity. OptionMetrics stores ``rate`` in percent, continuously compounded
(annualized); ``calc_benchmarks`` converts it to a decimal.

Notes
-----
- Before 2018 the curve is built from ICE LIBOR rates and CME Eurodollar
  futures settlements (IvyDB reference manual, zero curve section: verify the
  wording and check for a methodology change after LIBOR ended in 2023), so it
  serves as the LIBOR-implied benchmark ``libor_om``. Check it against the
  Eurodollar-futures curve (``GE``, from ``pull_databento``).
- The dates are filtered in SQL. They are written into the query as literals,
  after ``_iso_date`` checks that they parse as dates, so the same SQL runs on
  WRDS (Postgres) and in the offline test (SQLite), whose drivers use different
  placeholder syntax.
- One WRDS connection, so one Duo push, and no retries. The test that connects
  is marked ``@pytest.mark.wrds``.

Reuse: the ``zerocd`` part of HW3 ``src/pull_optionmetrics.py`` (one connection,
SQL tested against an in-memory SQLite database).
"""

from pathlib import Path

import pandas as pd

from settings import END_DATE, START_DATE, config

DATA_DIR = config("DATA_DIR")
OUTPUT_FILE = "optionm_zerocd.parquet"


def _iso_date(value):
    """Return ``value`` as a ``YYYY-MM-DD`` string; raise if it is not a date."""
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def zerocd_query(start=START_DATE, end=END_DATE):
    """SQL selecting ``date, days, rate`` from ``optionm_all.zerocd``, start to end."""
    return (
        "SELECT date, days, rate FROM optionm_all.zerocd "
        f"WHERE date BETWEEN '{_iso_date(start)}' AND '{_iso_date(end)}' "
        "ORDER BY date, days"
    )


def tidy_zerocd(df):
    """Fix the types of a raw ``zerocd`` result: datetime date, int days, float rate.

    Leaves the values in OptionMetrics' units (``rate`` in percent).
    """
    out = df[["date", "days", "rate"]].copy()
    out["date"] = pd.to_datetime(out["date"])
    out["days"] = out["days"].astype("int64")
    out["rate"] = out["rate"].astype("float64")
    return out.reset_index(drop=True)


def pull_zerocd(db, start=START_DATE, end=END_DATE):
    """Run the ``zerocd`` query on an open connection ``db`` (``wrds.Connection``)."""
    return tidy_zerocd(db.raw_sql(zerocd_query(start, end), date_cols=["date"]))


def connect_wrds():
    """Open one WRDS connection (one Duo push) as ``WRDS_USERNAME`` from ``.env``."""
    import wrds

    # cast=str: settings.config() passes cast=None through to decouple otherwise.
    return wrds.Connection(wrds_username=config("WRDS_USERNAME", default="", cast=str))


def load_zerocd(data_dir=DATA_DIR):
    """Load ``optionm_zerocd.parquet`` from ``data_dir``."""
    return pd.read_parquet(Path(data_dir) / OUTPUT_FILE)


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = connect_wrds()  # one Duo push
    try:
        df = pull_zerocd(db)
    finally:
        db.close()
    df.to_parquet(DATA_DIR / OUTPUT_FILE, index=False)
    print(
        f"zerocd: wrote {len(df)} rows, {df['date'].min():%Y-%m-%d} to "
        f"{df['date'].max():%Y-%m-%d}, days {df['days'].min()} to "
        f"{df['days'].max()}, to {DATA_DIR / OUTPUT_FILE}"
    )
