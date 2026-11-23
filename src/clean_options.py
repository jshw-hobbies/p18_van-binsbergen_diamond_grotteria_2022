"""Clean the raw OptionMetrics quotes into matched call-put pairs.

Domain A (options panel). Stage: clean. Docstring-only stub, to be filled in.

Input
-----
``DATA_DIR/opprcd_{SPX,DJX}_{YYYY}.parquet`` (from ``pull_optionmetrics``).

Outputs
-------
- ``DATA_DIR/clean_option_pairs.parquet``. Grain: date x index x exdate x
  strike. Columns: ``date, index, secid, root, settlement, exdate, days, ttm,
  strike, call_bid, call_ask, put_bid, put_ask, call_mid, put_mid``.
- ``DATA_DIR/option_filter_funnel.parquet``: the rows in and out of each
  filter, for the filter-funnel table.

Filters (starting proposal)
---------------------------
Each filter is a named function with a docstring giving its rationale, its own
unit test, and a log line ``rows_in -> rows_out``.

- F1 universe: divide ``strike_price`` by 1000 (OptionMetrics stores strike
  x 1000).
- F2 valid quotes: ``best_bid > 0`` and ``best_offer > best_bid``.
- F3 maturity: 30 <= days <= about 1100.
- F4 pairs: a call and a put on the same date, exdate, strike and root
  (settlement style). SPX (AM-settled) and SPXW (PM-settled) share a secid
  (verify), so never mix them.
- F5 spread cap: a relative-spread cap, or the paper's rule for the Nikkei:
  min ask <= 1.5 x max bid.
- F6 depth: at least N valid strike pairs per date and exdate (e.g. N = 5).

Units: ``ttm = days / 365`` (ACT/365).

Reuse: HW3 ``src/smile.py`` (``parity_forward``, the call/put pivot by strike).
"""
