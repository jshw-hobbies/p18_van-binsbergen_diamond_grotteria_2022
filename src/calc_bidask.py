"""Daily median relative bid-ask spreads of the options, by index and option type.

Domain D (microstructure and extension). Stage: calc. Docstring-only stub, to be
filled in.

Input
-----
``DATA_DIR/clean_option_pairs.parquet`` (from ``clean_options``).

Output
------
``DATA_DIR/bidask_daily.parquet``. Grain: date x index x cp. Column:
``med_rel_spread``, the daily median of (ask - bid) / mid.

Used in Table 7 (WP numbering): the DJX - SPX box-rate spread regressed on log
bid-ask spreads.
"""
