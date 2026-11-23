"""Treasury market spreads for Table 11, from CRSP Treasury quotes and the GSW curve.

Domain C (Treasuries and monetary policy). Stage: calc. Docstring-only stub, to be
filled in.

Inputs
------
``DATA_DIR/crsp_tfz_dly.parquet`` and ``crsp_tfz_iss.parquet`` (from
``pull_crsp_treasury``), and ``gsw_yield_curve.parquet`` (from ``pull_gsw``).

Output
------
``DATA_DIR/treasury_spreads.parquet`` (long). Grain: date x spread. Column:
``value_bp``.

Spreads
-------
CRSP replaces the paper's GovPX data.

- 6-month: notes and bonds maturing within 6 months, against bills with the same
  maturity date. The daily median of the continuously compounded yield
  difference.
- On-the-run: the most recently issued 10-year note's yield minus its GSW-model
  yield.
- Notes vs bonds: among securities with 3 to 10 years left, the median model
  residual of notes minus that of bonds. Bonds are those with an original
  maturity over 10 years.
- STRIPS: not in CRSP. Use Bloomberg or drop it (ask the professor).

Reuse: the course's ``fed_yield_curve`` repo, ``src/gsw_pricing.py``
(``actual_vs_predicted_yields``); HW2 ``calc_runness``.
"""
