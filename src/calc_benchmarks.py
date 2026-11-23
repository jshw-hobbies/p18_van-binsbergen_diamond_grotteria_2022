"""Build the benchmark rates the box rates are compared with, on the same tenors.

Domain B (benchmark rates). Stage: calc. Docstring-only stub, to be filled in.

Inputs
------
- ``DATA_DIR/gsw_yield_curve.parquet``, ``fred.parquet``,
  ``optionm_zerocd.parquet`` and ``futures_daily.parquet``.
- Optional Bloomberg exports in ``DATA_DIR/manual/`` (OIS, GC repo before
  2018). If one is missing, print a clear message and leave its rows out, so
  the tables show n/a. Raw Bloomberg data never goes into git.

Output
------
``DATA_DIR/benchmark_rates.parquet`` (long). Grain: date x source x tenor_m.
Column: ``rate``. ``source`` is one of ``gsw, libor_om, ois_bbg, tbill, gc_repo,
sofr, zq_implied, sofr_fut_implied, ge_implied``, ...

Conversions
-----------
Every rate becomes a decimal, continuously compounded, with maturities on
ACT/365:

- LIBOR is simple ACT/360: r = (365 / d) ln(1 + L d / 360).
- T-bills are quoted as discount yields: convert them before comparing.
- GSW ``SVENYxx`` yields are in percent and annual only: compute 3, 6 and 18
  months from the Svensson parameters (``svensson_spot``).
- Futures are not swaps. Fed funds futures settle on the monthly average rate,
  OIS compounds daily, and futures carry a small convexity bias. Say so
  wherever the futures-implied rates are used.

Reuse: the course's ``fed_yield_curve`` repo, ``src/gsw_pricing.py``
(``svensson_spot``); HW2 ``src/fedwatch.py`` (``ZQ`` symbol parsing).
"""
