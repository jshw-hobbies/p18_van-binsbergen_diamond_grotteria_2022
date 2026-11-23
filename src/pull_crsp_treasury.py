"""Pull CRSP Treasury daily quotes and issue information from WRDS, bills included.

Domain C (Treasuries and monetary policy). Stage: pull. Docstring-only stub, to be
filled in.

What it pulls
-------------
``crspm.tfz_dly`` (daily quotes) and ``crspm.tfz_iss`` (issue information), from
``START_DATE`` to ``END_DATE``, filtered in SQL.

Outputs
-------
``DATA_DIR/crsp_tfz_dly.parquet`` and ``DATA_DIR/crsp_tfz_iss.parquet``, raw.

Notes
-----
- HW2's pull uses ``itype IN (1, 2)``, which excludes bills. Table 11's 6-month
  spread needs bills (verify the ``itype`` codes).
- CRSP replaces the paper's GovPX data. STRIPS are not in CRSP.
- One WRDS connection, so one Duo push. Mark WRDS tests ``@pytest.mark.wrds``.

Reuse: HW2 ``src/pull_CRSP_treasury.py`` (and its ``calc_runness``, for
on-the-run status).
"""
