# CLAUDE.md: P18 Risk-Free Interest Rates

Shared instructions for every Claude Code session in this repo, and a two-minute orientation for the
four of us. If a rule here gets in your way, open a PR that changes this file. Don't work around it.

## The project

FINM 32800 final project P18. We replicate van Binsbergen, Diamond and Grotteria, "Risk-free interest
rates" (JFE 2022).

- **Paper version:** work from **NBER WP 26138 (Aug 2019)**, whose table numbers match our task list.
  The JFE version numbers its tables differently.
- **The idea:** a box spread on SPX or DJX options pays a fixed amount whatever the index does, so its
  price gives a risk-free discount rate with no convenience yield. We compare that rate with Treasury,
  OIS, LIBOR/SOFR and repo rates.
- **Exhibits (WP numbering):** Tables 1 and 3 are the box-rate panels and the data-cleaning deliverable.
  We also do Tables 2, 4, 7, 9 and 11, an update to the latest OptionMetrics date (`END_DATE`,
  2025-08-29 as of Nov 2026), and one extension.
- **Grading:** the professor clones the repo and runs `doit` from scratch. He grades `main` as it stood
  24 hours before our final meeting (no later than Fri 2026-12-11), and he questions every member on
  every module.

## Commands (run from the repo root)

```
uv sync              # build .venv from uv.lock (Python 3.12, pinned in .python-version)
uv run doit          # run the pipeline; only tasks whose inputs changed rerun
uv run doit list     # list the tasks
uv run doit -v 2     # show each task's output live (use this when a task seems stuck)
uv run pytest        # run the tests (skips the WRDS ones; `-m wrds` runs only those)
uv run ruff check .  # lint, as CI does; `--fix` repairs import order and unused imports
uv add <package>     # add a dependency (updates pyproject.toml and uv.lock); never pip install
```

- Always use `uv run ...`. A plain `python` may be Anaconda's or another project's venv.
- doit reads `dodo.py` from the current folder, so run it from the repo root.
- Copy `.env.example` to `.env` and fill in your own values. `.env` is gitignored.

## Hard rules

1. **Never commit data.** Nothing from WRDS, Bloomberg, Databento or any other vendor, not even a small
   sample or a test fixture. Git keeps history, so a file deleted later still counts. Test fixtures are
   synthetic.
2. **Never print, log or commit credentials** (`.env` values, API keys, passwords). `.env.example` keeps
   its values blank.
3. **WRDS: no retry loops.** Every connection attempt sends a Duo push to the account owner. Ask the human
   before running anything that connects to WRDS. Pull OptionMetrics one year at a time, with SQL
   filters; never select a whole `opprcd` table.
4. **Databento: keep the cost guard.** Every pull goes through `assert_query_is_free`, unchanged; never
   weaken or bypass it. Without the human's explicit OK:
   - call only the free metadata endpoints (`get_dataset_range`, `get_cost`, `get_record_count`);
   - call data endpoints only when `get_cost` returns $0.00.

   Pull intraday data only for event windows, never whole histories.
5. **Fix tolerances before results exist.** Never edit `paper_values.py` or a tolerance test to make a
   test pass; a failing replication test is a finding to report. Transcribe paper values by hand from the
   PDF, never with AI.
6. **Determinism.** `START_DATE`, `END_DATE` and other parameters are committed constants in
   `src/settings.py`. `.env` holds only secrets and machine-specific paths.
7. **Windows-safe code.** At least one of us works on Windows:
   - use `pathlib`;
   - no `%-d`-style `strftime` flags;
   - no spaces in paths, and quote paths in `dodo.py` actions.
8. **Never push to `main`.** Once branch protection is on:
   - work on a branch named `<github-handle>/<topic>`;
   - open a PR, and merge only after one approval and green CI;
   - never force-push to `main`.

## Pipeline conventions

- **Stages.** Each stage only reads the previous stage's output and never edits it:
  - `pull_*.py` writes raw data to `DATA_DIR` once;
  - `clean_*.py` makes tidy data;
  - `calc_*.py` does the analysis;
  - table and chart scripts write to `OUTPUT_DIR`.
- **doit tasks.** Every task in `dodo.py` declares its `file_dep` and `targets`. Use `config_changed` for
  parameters, so that changing a constant reruns what depends on it.
  - Pulls never `file_dep` on `settings.py`: editing a comment there must not re-pull from WRDS.
  - Every P18 task is already declared, but a plain `doit` runs only `DOIT_CONFIG["default_tasks"]`. The PR
    that implements a module adds its task to that list. Until then, run it by name: `doit pull_gsw`.
- **Filters.** Each option-data filter is a named function with:
  - a docstring giving its rationale;
  - its own unit test;
  - a log line `rows_in -> rows_out`, which feeds the filter-funnel table.
- **Units.** Store rates as decimals, continuously compounded, with maturities on ACT/365. Convert other
  conventions in the clean stage and say so in the docstring: LIBOR is simple ACT/360, T-bills are
  quoted as discount yields, and GSW yields are in percent.
- **Time zones.** Databento timestamps are UTC, and FOMC times are US Eastern. Convert with
  `America/New_York`, and test across a daylight-saving change.
- **Tests.** Mark tests that need WRDS or other credentials with `@pytest.mark.wrds`. A plain
  `uv run pytest` skips them (`addopts` in `pyproject.toml`), and so do CI and `doit`. Run them on purpose
  with `uv run pytest -m wrds`, which sends a Duo push, so ask the human first. Everything else runs on
  synthetic fixtures. A misspelled marker is an error (`--strict-markers`).
- **Report.** Every number in the LaTeX report comes from a generated `.tex` file through `\input`. No
  hand-typed statistics.

## Data contracts (draft: change them by PR)

These are tidy parquet files in `DATA_DIR`. They let us build in parallel, against mock data until the
real data exists.

| Dataframe | Grain | Columns |
|---|---|---|
| `clean_option_pairs` | date × index × exdate × strike | `date, index, secid, root, settlement, exdate, days, ttm, strike, call_bid, call_ask, put_bid, put_ask, call_mid, put_mid` |
| `option_filter_funnel` | index × filter | `filter, rows_in, rows_out` (one row per filter F1–F6, in order) |
| `box_rates_by_expiry` | date × index × exdate | `rate_ts, rate_ols, r2_ols, se_ols, n_strikes, n_pairs, days, ttm` |
| `box_rates_fixed_tenor` | date × index × tenor_m | `rate` |
| `benchmark_rates` (long) | date × source × tenor_m | `rate`; `source` ∈ {gsw, libor_om, ois_bbg, tbill, gc_repo, sofr, zq_implied, sofr_fut_implied, ge_implied, …} |
| `bidask_daily` | date × index × cp | `med_rel_spread` |
| `zq_event_trades` | event × trade | `event_id, ts_utc, ts_et, symbol, price, size` (announcement windows only) |
| `fomc_surprises` | event | `date, time_et, scheduled, surprise, contract_used, method ∈ {intraday, daily}, source ∈ {databento, bloomberg}` |
| `treasury_spreads` (long) | date × spread | `value_bp` |

## Layout

- **`src/`** holds the code. `settings.py` holds the paths and the committed constants (`START_DATE`,
  `END_DATE`, the secids, `TENORS_M`, ...).
  - The module map: `pull_optionmetrics`, `pull_zerocd`, `pull_gsw`, `pull_fred`, `pull_crsp_treasury`,
    `pull_databento`, `clean_options`, `calc_box_rates`, `calc_benchmarks`, `calc_bidask`,
    `calc_fomc_surprises`, `calc_treasury_arbitrage`, `calc_tables`. Each starts as a docstring-only stub
    that says what it reads, what it writes (the data contract) and what code to reuse. Fill in the stub;
    don't start a new file.
- **`data_manual/`** holds small hand-made inputs we're allowed to commit, such as the FOMC calendar.
  Never vendor data.
- **`reports/`** holds the LaTeX report. For now it has the template's example reports, which get replaced
  once ours exists.
- **`docs_src/` and `chartbook.toml`** build the ChartBook site.
- **`_data/`, `_output/` and `docs/`** are generated and gitignored.

## Working with Claude in this repo

- Keep diffs small. Start from the data contract and a failing test.
- After writing code, explain the diff so the human can defend every line at the final meeting.
- Say so in the PR if you add a dependency, change a constant in `settings.py`, or touch a module
  someone else owns.
- Reuse course code (the HW2/HW3 pulls) rather than rewriting it, and note where it came from.

## Known gotchas

- **WRDS returns `secid` as a float** (`102456.0`). Cast it to int before you filter or merge on it.
- **Python 3.12 is pinned** in `.python-version`. Without the pin, uv may pick 3.14, which can't install
  the template's `numpy==1.26.4`.
- **`pyarrow` is capped at `<26`**, because pyarrow 26 requires NumPy 2.
- **TinyTeX lacks some packages the reports need.** Install them with:
  `tlmgr install preprint accents adjustbox collectbox appendix appendixnumberbeamer bbm bbm-macros cancel caption ccicons jknapltx bbold bbold-type1 rsfs mathtools pbox pdflscape pgfplots placeins setspace silence siunitx soul tabulary threeparttable tocbibind todonotes xargs xkeyval beamer translator beamertheme-metropolis pgfopts`.
  After installing a missing package, run `latexmk -C` inside `reports/`: latexmk remembers a failed run
  and won't retry otherwise.
- **`thmtools` is disabled** in `reports/my_common_header.sty`, because it breaks on the 2026 LaTeX
  kernel.
- **VS Code may activate another project's venv.** uv warns and ignores it. Opening this repo as its own
  VS Code window avoids this.
- **git shows long output in a pager.** Press `q` to exit.
