"""Write the report's tables as LaTeX files, from the calc stage's outputs.

All domains: each owner adds the functions for their own tables. Stage: tables.
Docstring-only stub, to be filled in.

Inputs
------
From ``DATA_DIR``: ``box_rates_fixed_tenor``, ``benchmark_rates``,
``bidask_daily``, ``fomc_surprises``, ``treasury_spreads`` and
``option_filter_funnel`` (parquet).

Outputs
-------
``OUTPUT_DIR/tables/table_{N}.tex`` for Tables 1, 2, 3, 4, 7, 9 and 11 (NBER WP
26138 numbering), and ``OUTPUT_DIR/tables/filter_funnel.tex``. The report pulls
them in with ``\\input``, so it has no hand-typed numbers.

Replication tests compare these numbers with ``src/paper_values.py``, within
tolerances fixed before the results exist.
"""
