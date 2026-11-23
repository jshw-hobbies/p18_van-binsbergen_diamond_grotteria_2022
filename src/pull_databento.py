"""Pull CME futures from Databento: daily bars, and fed funds trades around FOMC news.

Domain C (Treasuries and monetary policy). Stage: pull. Docstring-only stub, to be
filled in. This is the shared Databento module: domain B uses its daily bars.

What it pulls
-------------
From ``DATABENTO_DATASET`` (CME Globex), all free under the course subscription:

- daily bars for ``ZQ`` (fed funds), ``SR1`` and ``SR3`` (SOFR) and ``GE``
  (Eurodollar, to 2023), for the futures-implied rates in ``calc_benchmarks``;
- every ``ZQ`` trade within ``FOMC_WINDOW_MINUTES`` of each announcement in
  ``data_manual/fomc_announcements.csv``, for ``calc_fomc_surprises``.

Outputs
-------
- ``DATA_DIR/futures_daily.parquet``: the daily bars, raw.
- ``DATA_DIR/zq_event_trades.parquet``: ``event_id, ts_utc, ts_et, symbol,
  price, size``, for the announcement windows only.

Rules
-----
- Every request goes through ``assert_query_is_free``, unchanged. It calls
  ``get_cost`` first and refuses anything above $0.00.
- Pull intraday data only for event windows, never whole histories.
- Databento timestamps are UTC, and FOMC times are US Eastern. Convert with
  ``America/New_York``, and test across a daylight-saving change.
- CME data starts on 2010-06-06; earlier surprises need Bloomberg.
- The ``ZQ.FUT`` parent also returns calendar spreads: keep only outright
  contracts.

Reuse: HW2 ``src/pull_fed_funds_futures.py`` (``assert_query_is_free``) and
``src/fedwatch.py`` (``filter_outright_contracts``, ``ZQ`` symbol parsing).
"""
