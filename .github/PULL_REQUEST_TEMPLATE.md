## What this PR does

<!-- One or two sentences, and the issue it closes, e.g. "Closes #12". -->

## How to check it

<!-- The commands a reviewer runs, e.g. `uv run pytest src/test_calc_box_rates.py`
or `uv run doit calc_box_rates`. -->

## Checklist

- [ ] **Tests:** new code has unit tests on synthetic data, and `uv run pytest` passes.
      Tests that need WRDS or other credentials are marked `@pytest.mark.wrds`.
- [ ] **Docstrings:** every new module and function has one, with units, and each
      filter's docstring gives its rationale.
- [ ] **No data, no credentials:** nothing from WRDS, Bloomberg, Databento or any other
      vendor (not even a sample), and no `.env` values or API keys.
- [ ] **Paper values and tolerances:** `paper_values.py` and the tolerance tests are
      unchanged, or this PR explains why.
- [ ] **`dodo.py`:** the task's `file_dep` and `targets` match the module, and an
      implemented module's task is in `DOIT_CONFIG["default_tasks"]`.
- [ ] **`chartbook.toml`** is updated for any new dataframe, chart or notebook.
- [ ] `uv run doit` runs green from the repo root.

## Call-outs

<!-- List any of these, or write "None": a new dependency, a changed constant in
`settings.py`, a changed data contract, or a change to a module someone else owns. -->
