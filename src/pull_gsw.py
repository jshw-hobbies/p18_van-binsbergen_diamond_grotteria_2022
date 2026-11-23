"""Download the Gurkaynak, Sack and Wright (2007) Treasury yield curve from the Fed.

Domain B (benchmark rates). Stage: pull. Docstring-only stub, to be filled in.

Source
------
The Federal Reserve's ``feds200628.csv``: daily, free, no credentials.

Output
------
``DATA_DIR/gsw_yield_curve.parquet``, raw:

- the zero-coupon yields ``SVENYxx``: continuously compounded, in percent, at
  annual maturities only;
- the Svensson parameters (``BETA0`` to ``BETA3``, ``TAU1``, ``TAU2``), from
  which ``calc_benchmarks`` computes the 3-, 6- and 18-month yields.

Reuse: HW2 ``src/pull_yield_curve_data.py`` (the download); the course's
``fed_yield_curve`` repo, ``src/gsw_pricing.py`` (``svensson_spot``).
"""
