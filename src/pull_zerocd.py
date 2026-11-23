"""Pull the OptionMetrics zero-coupon yield curve (``optionm_all.zerocd``) from WRDS.

Domain B (benchmark rates). Stage: pull. Docstring-only stub, to be filled in.

Output
------
``DATA_DIR/optionm_zerocd.parquet``: ``date, days, rate``, raw. OptionMetrics
stores ``rate`` in percent; ``calc_benchmarks`` converts it.

Notes
-----
- Before 2018 the curve is built from LIBOR and Eurodollar futures (verify in
  the IvyDB reference manual), so it serves as the LIBOR-implied benchmark.
  Check it against the Eurodollar-futures curve (``GE``, from
  ``pull_databento``).
- Filter the dates (``START_DATE`` to ``END_DATE``) in SQL.
- One WRDS connection, so one Duo push. Mark WRDS tests ``@pytest.mark.wrds``.

Reuse: HW3 ``src/pull_optionmetrics.py``, which also pulls ``zerocd``.
"""
