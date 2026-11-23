"""Pull benchmark rate series from FRED.

Domain B (benchmark rates). Stage: pull. Docstring-only stub, to be filled in.

Series
------
To be chosen. Candidates: SOFR, BGCR and TGCR (repo rates, from 2018), T-bill
rates, and constant-maturity Treasury yields (to cross-check GSW). OIS is
probably not on FRED (verify).

Output
------
``DATA_DIR/fred.parquet``: one column per series, raw, in the units FRED
publishes (mostly percent). ``calc_benchmarks`` converts them.

Reuse: the midterm report's ``src/pull_fred.py``.
"""
