"""Pull SPX and DJX option quotes from OptionMetrics on WRDS, one year at a time.

Domain A (options panel). Stage: pull. Docstring-only stub, to be filled in.

What it pulls
-------------
``optionm_all.opprcd{YYYY}`` for ``secid IN (SPX_SECID, DJX_SECID)`` and dates
from ``START_DATE`` to ``END_DATE`` (``settings.py``), filtered in SQL, one year
per query. Never select a whole ``opprcd`` table.

Output
------
``DATA_DIR/opprcd_{SPX,DJX}_{YYYY}.parquet``: the raw rows, unmodified. All
cleaning happens in ``clean_options``.

Notes
-----
- Open one WRDS connection for all the years: every connection sends a Duo
  push, and there are no retry loops.
- ``strike_price`` is stored as strike x 1000; ``clean_options`` divides it.
- WRDS returns ``secid`` as a float: cast it to int.
- Mark tests that connect to WRDS with ``@pytest.mark.wrds``.

Reuse: HW3 ``src/pull_optionmetrics.py`` (a year-by-year pull, with its SQL
tested against in-memory SQLite).
"""
