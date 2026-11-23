# Risk-Free Interest Rates: a replication of van Binsbergen, Diamond and Grotteria (2022)

FINM 32800 final project P18, University of Chicago.

> **Status (November 2026): setting up.** The pipeline's modules in `src/` are
> documented stubs that the team is filling in. For now, `doit` runs the tests and
> builds the template report and site. Each module's task joins `doit` once the
> module is implemented.

## Summary

A box spread combines four SPX (or DJX) options so that it pays a fixed amount at
expiry, whatever the index does. Its price is therefore a risk-free discount factor,
and the rate it implies carries no convenience yield. The paper estimates these box
rates and compares them with Treasury, OIS, LIBOR and repo rates. The gap between the
box rate and the Treasury yield measures the convenience yield on Treasuries: about
40 basis points in the paper.

We replicate the paper's main tables with end-of-day OptionMetrics quotes, extend them
to the latest date available, and add one extension.

## The paper

Jules H. van Binsbergen, William F. Diamond and Marco Grotteria, "Risk-free interest
rates", *Journal of Financial Economics* 143 (2022), 1–29.

We work from the working-paper version, [NBER Working Paper 26138](https://www.nber.org/papers/w26138)
(August 2019). Table numbers here follow it; the JFE version numbers its tables
differently.

## What we replicate

The replication sample runs from 2004-01-01 to 2018-12-31. The update repeats the
same exhibits through 2025-08-29, the last date of OptionMetrics on WRDS as of
November 2026.

| Exhibit (WP numbering) | Content |
|---|---|
| Table 1 | SPX box rates at 6, 12 and 18 months, against LIBOR, Treasury (GSW) and OIS rates |
| Table 2 | 3-month rates: box, Treasury, OIS and GC repo |
| Table 3 | DJX box rates against Treasury yields |
| Table 4 | DJX minus SPX box rates: mean, standard deviation and AR(1) |
| Table 7 | The DJX minus SPX spread regressed on log bid-ask spreads |
| Table 9 | Responses of box and Treasury rates to FOMC policy surprises |
| Table 11 | Treasury market spreads: 6-month, on-the-run, and notes vs bonds |

## Setup and running

### Prerequisites

- [uv](https://docs.astral.sh/uv/) and git. uv installs Python 3.12 (pinned in
  `.python-version`) and the exact package versions in `uv.lock`.
- A LaTeX distribution with `xelatex` and `latexmk` (TeX Live, MiKTeX or TinyTeX).
  TinyTeX needs these extra packages:

  ```
  tlmgr install preprint accents adjustbox collectbox appendix appendixnumberbeamer bbm bbm-macros cancel caption ccicons jknapltx bbold bbold-type1 rsfs mathtools pbox pdflscape pgfplots placeins setspace silence siunitx soul tabulary threeparttable tocbibind todonotes xargs xkeyval beamer translator beamertheme-metropolis pgfopts
  ```

- For the data pulls:
  - a **WRDS** account with OptionMetrics and CRSP. Set up a `pgpass` file so that
    the pulls run without a password prompt. Each connection sends a Duo push;
  - a **Databento** API key (the course subscription). The pulls use only free CME
    data and check the cost before every request.

### Run

```
git clone https://github.com/jshw-hobbies/p18_van-binsbergen_diamond_grotteria_2022.git
cd p18_van-binsbergen_diamond_grotteria_2022
uv sync
cp .env.example .env        # on Windows: copy .env.example .env
```

Fill in `WRDS_USERNAME` and `DATABENTO_API_KEY` in `.env`, then run:

```
uv run doit
```

`doit` reruns only the tasks whose inputs changed. Other commands:

```
uv run doit list         # list every task in the pipeline
uv run doit <task>       # run one task, e.g. uv run doit pull_gsw
uv run pytest            # run the tests
uv run ruff check .      # lint
```

The sample dates, security IDs and tenors are committed constants in
`src/settings.py`, not `.env` settings, so the same commit gives the same results on
every machine. `.env` holds only credentials and, optionally, `DATA_DIR`.

### Outputs

- `_data/`: pulled and cleaned data (gitignored).
- `_output/tables/`: the tables, as LaTeX files.
- `reports/`: the LaTeX report and its PDF.
- `docs/`: the ChartBook site.

## Data sources

| Source | Data | Access | Used for |
|---|---|---|---|
| OptionMetrics IvyDB US (WRDS) | SPX (secid 108105) and DJX (secid 102456) option quotes; the zero-coupon curve `zerocd` | WRDS | Box rates; LIBOR-implied benchmark |
| Federal Reserve: Gürkaynak, Sack and Wright (2007) | Treasury zero-coupon yields and Svensson parameters | Free | Government benchmark; model yields for Table 11 |
| FRED | SOFR, BGCR, TGCR, T-bill and constant-maturity Treasury yields | Free | Benchmarks, especially after 2018 |
| CRSP Treasury (WRDS) | Daily Treasury quotes and issue information | WRDS | Table 11 |
| Databento, CME Globex | Fed funds (`ZQ`), SOFR (`SR1`, `SR3`) and Eurodollar (`GE`) futures; `ZQ` trades around FOMC announcements | Course key, free | Futures-implied rates; FOMC surprises from 2010 |
| Bloomberg (manual export) | OIS; GC repo before 2018; fed funds futures before 2010 | Lab terminal | Benchmarks and surprises where no free source exists |
| `data_manual/fomc_announcements.csv` | FOMC announcement dates and times | Hand-built | Table 9 |

Raw Bloomberg data is copyrighted and never goes into git. The exports go to
`DATA_DIR/manual/`, and the pipeline treats them as optional.

## Deviations from the paper

- **End-of-day quotes instead of minute-level ones.** The paper estimates a box rate
  every minute from CBOE quotes and takes the daily median. We use OptionMetrics'
  end-of-day quotes, so our rates are noisier day to day.
- **CRSP instead of GovPX** for the Treasury spreads in Table 11. STRIPS are not in
  CRSP.
- **Table 9 is a daily adaptation** (pending the professor's approval). Our box rates
  are end-of-day, so their responses are measured over days, not minutes. The surprises use the paper's intraday window
  from June 2010 (Databento) and daily data before that (Bloomberg).
- **Futures-implied stand-ins.** From 2010, rates implied by fed funds futures stand
  in for OIS where Bloomberg data is missing. Futures are not swaps: they settle on a
  monthly average rate and carry a small convexity bias.
- **The update uses SOFR**, because LIBOR ended in 2023.

## Extension

To be agreed with the professor. The leading candidate asks whether the box rate's
convenience yield can actually be earned after trading costs, using executable
(bid/ask) box rates, Cboe's box spread quotes and the BOXX ETF.

## Repository layout

- `src/`: the code. `settings.py` holds the paths and committed constants. The
  modules follow the stages `pull_*` (raw data), `clean_*` (tidy data), `calc_*`
  (analysis) and `calc_tables` (LaTeX tables).
- `dodo.py`: the pipeline. Every task declares its inputs and outputs.
- `data_manual/`: small hand-made inputs that are committed, such as the FOMC calendar.
- `reports/`: the LaTeX report.
- `docs_src/` and `chartbook.toml`: the ChartBook site.

## Team

Joe, Leila, Adam and Lamiya. On GitHub: jshw-hobbies, lhuang28, adamsun09 and
lbadalova-un. Each member owns one data domain, from pull to tables (to be assigned).
