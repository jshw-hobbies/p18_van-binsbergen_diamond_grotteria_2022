"""Estimate box-spread rates for each date and expiry, then interpolate to fixed tenors.

Domain A (options panel). Stage: calc. Docstring-only stub, to be filled in.

Input
-----
``DATA_DIR/clean_option_pairs.parquet`` (from ``clean_options``).

Outputs
-------
- ``DATA_DIR/box_rates_by_expiry.parquet``. Grain: date x index x exdate.
  Columns: ``rate_ts, rate_ols, r2_ols, se_ols, n_strikes, n_pairs, days, ttm``.
- ``DATA_DIR/box_rates_fixed_tenor.parquet``. Grain: date x index x tenor_m,
  for the tenors in ``TENORS_M``. Column: ``rate``.

Estimator
---------
The paper's Estimator 2 (Theil-Sen), for each date and expiry:

1. Form every strike pair i, j with K_i > K_j.
2. Compute the slope [(P_i - C_i) - (P_j - C_j)] / (K_i - K_j).
3. Take the median slope: it estimates the discount factor.
4. Convert to a rate: r = -ln(median) / ttm.

OLS (Estimator 1) gives ``r2_ols`` and ``se_ols`` as diagnostics.

Fixed tenors: interpolate linearly between the two expiries that bracket each
tenor (WP footnote 7). Never extrapolate, and require the bracketing expiries to
lie within a maximum gap.

Units: rates are decimals, continuously compounded, with maturities on ACT/365.

Write this test first: a synthetic box priced at r = 3% must come back as 3%.
"""
