"""Monetary policy surprises for every FOMC announcement, from fed funds futures.

Domain C (Treasuries and monetary policy). Stage: calc. Docstring-only stub, to be
filled in.

Inputs
------
- ``data_manual/fomc_announcements.csv``: the hand-built calendar, with times in
  US Eastern, including unscheduled meetings.
- ``DATA_DIR/zq_event_trades.parquet`` (from ``pull_databento``), from 2010-06.
- Optional: Bloomberg ``FF1`` / ``FF2 Comdty`` daily closes in
  ``DATA_DIR/manual/``, for 2004 to 2010-05.

Output
------
``DATA_DIR/fomc_surprises.parquet``. Grain: one row per event. Columns:
``date, time_et, scheduled, surprise, contract_used, method, source``, with
``method`` in {intraday, daily} and ``source`` in {databento, bloomberg}.

Surprise
--------
Kuttner (2001), as the paper uses it. Let f = 100 - the futures price, d = the
announcement's day of the month and D = the number of days in the month. Use
the change in the current-month contract, scaled by D / (D - d). If the
announcement falls in the last 7 days of the month, use the next-month contract,
unscaled. HW2's FedWatch code uses a 3-day rule: don't copy it.

The change is measured:

- intraday (Databento, 2010-06 on): from the last trade at least 10 minutes
  before the announcement to the first trade at least 20 minutes after (WP
  section 8);
- daily (Bloomberg, 2004 to 2010-05): close to close on the announcement day.

Feeds Table 9, whose daily adaptation needs the professor's OK.

Reuse: HW2 ``src/fedwatch.py`` (``ZQ`` symbol parsing and the n / (n - d)
weighting; change it to the 7-day rule).
"""
