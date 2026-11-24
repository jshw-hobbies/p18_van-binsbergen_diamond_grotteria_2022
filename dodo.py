"""Run or update the project. This file uses the `doit` Python package. It works
like a Makefile, but is Python-based

"""

#######################################
## Configuration and Helpers for PyDoit
#######################################
## Make sure the src folder is in the path
import sys

sys.path.insert(1, "./src/")

import shutil
from os import environ
from pathlib import Path

from doit.tools import config_changed

from settings import (
    DATABENTO_DATASET,
    DJX_SECID,
    END_DATE,
    FOMC_WINDOW_MINUTES,
    SPX_SECID,
    START_DATE,
    TENORS_M,
    config,
)

## `doit` with no arguments runs only default_tasks. Every P18 task is declared
## below (see `doit list`), but a task joins this list only in the PR that
## implements its module, so `doit` stays green while modules are stubs.
## Run any task by name: `doit pull_gsw`.
DOIT_CONFIG = {
    "backend": "sqlite3",
    "dep_file": "./.doit-db.sqlite",
    "default_tasks": [
        "config",
        "pull_gsw",
        "pull_fred",
        "run_notebooks",
        "compile_latex_docs",
        "build_chartbook_site",
        "run_pytest",
    ],
}


BASE_DIR = config("BASE_DIR")
DATA_DIR = config("DATA_DIR")
MANUAL_DATA_DIR = config("MANUAL_DATA_DIR")
OUTPUT_DIR = config("OUTPUT_DIR")
OS_TYPE = config("OS_TYPE")

## Helpers for handling Jupyter Notebook tasks
environ["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"

# fmt: off
## Helper functions for automatic execution of Jupyter notebooks
def jupyter_execute_notebook(notebook_path):
    return f"jupyter nbconvert --execute --to notebook --ClearMetadataPreprocessor.enabled=True --inplace {notebook_path}"
def jupyter_to_html(notebook_path, output_dir=OUTPUT_DIR):
    return f"jupyter nbconvert --to html --output-dir={output_dir} {notebook_path}"
def jupyter_to_md(notebook_path, output_dir=OUTPUT_DIR):
    """Requires jupytext"""
    return f"jupytext --to markdown --output-dir={output_dir} {notebook_path}"
def jupyter_clear_output(notebook_path):
    """Clear the output of a notebook"""
    return f"jupyter nbconvert --ClearOutputPreprocessor.enabled=True --ClearMetadataPreprocessor.enabled=True --inplace {notebook_path}"
# fmt: on


def mv(from_path, to_path):
    """Move a file to a folder"""
    from_path = Path(from_path)
    to_path = Path(to_path)
    to_path.mkdir(parents=True, exist_ok=True)
    if OS_TYPE == "nix":
        command = f"mv {from_path} {to_path}"
    else:
        command = f"move {from_path} {to_path}"
    return command


def copy_file(origin_path, destination_path, mkdir=True):
    """Create a Python action for copying a file."""

    def _copy_file():
        origin = Path(origin_path)
        dest = Path(destination_path)
        if mkdir:
            dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, dest)

    return _copy_file


##################################
## Begin rest of PyDoit tasks here
##################################


def task_config():
    """Create empty directories for data and output if they don't exist"""
    return {
        "actions": ["python ./src/settings.py"],
        "targets": [DATA_DIR, OUTPUT_DIR],
        "file_dep": ["./src/settings.py"],
        "clean": [],
    }


##################################
## P18 pipeline: pull -> clean -> calc -> tables
##################################
## Each task declares its file_dep and targets, so doit reruns exactly what
## changed. Pulls depend on the parameters they use through config_changed, not
## on settings.py itself: editing a comment in settings.py must not re-pull years
## of OptionMetrics (and send Duo pushes). Raw pulls set "clean": [] so that
## `doit clean` never deletes them.

INDEXES = {"SPX": SPX_SECID, "DJX": DJX_SECID}
YEARS = range(int(START_DATE[:4]), int(END_DATE[:4]) + 1)
SAMPLE = {"START_DATE": START_DATE, "END_DATE": END_DATE}

OPPRCD = [DATA_DIR / f"opprcd_{i}_{y}.parquet" for i in INDEXES for y in YEARS]
ZEROCD = DATA_DIR / "optionm_zerocd.parquet"
GSW = DATA_DIR / "gsw_yield_curve.parquet"
FRED = DATA_DIR / "fred.parquet"
FUTURES_DAILY = DATA_DIR / "futures_daily.parquet"
ZQ_EVENT_TRADES = DATA_DIR / "zq_event_trades.parquet"
CRSP_TREASURY = [DATA_DIR / "crsp_tfz_dly.parquet", DATA_DIR / "crsp_tfz_iss.parquet"]
FOMC_CALENDAR = MANUAL_DATA_DIR / "fomc_announcements.csv"

CLEAN_OPTION_PAIRS = DATA_DIR / "clean_option_pairs.parquet"
FILTER_FUNNEL = DATA_DIR / "option_filter_funnel.parquet"
BOX_RATES_BY_EXPIRY = DATA_DIR / "box_rates_by_expiry.parquet"
BOX_RATES_FIXED_TENOR = DATA_DIR / "box_rates_fixed_tenor.parquet"
BIDASK_DAILY = DATA_DIR / "bidask_daily.parquet"
BENCHMARK_RATES = DATA_DIR / "benchmark_rates.parquet"
FOMC_SURPRISES = DATA_DIR / "fomc_surprises.parquet"
TREASURY_SPREADS = DATA_DIR / "treasury_spreads.parquet"

TABLES = [OUTPUT_DIR / "tables" / f"table_{n}.tex" for n in (1, 2, 3, 4, 7, 9, 11)]
FUNNEL_TABLE = OUTPUT_DIR / "tables" / "filter_funnel.tex"


def task_pull_optionmetrics():
    """Pull SPX and DJX option quotes from OptionMetrics (WRDS), year by year"""
    return {
        "actions": ["python ./src/pull_optionmetrics.py"],
        "file_dep": ["./src/pull_optionmetrics.py"],
        "targets": OPPRCD,
        "uptodate": [config_changed({**SAMPLE, "INDEXES": INDEXES})],
        "clean": [],
    }


def task_pull_zerocd():
    """Pull the OptionMetrics zero-coupon curve (WRDS)"""
    return {
        "actions": ["python ./src/pull_zerocd.py"],
        "file_dep": ["./src/pull_zerocd.py"],
        "targets": [ZEROCD],
        "uptodate": [config_changed(SAMPLE)],
        "clean": [],
    }


def task_pull_gsw():
    """Download the GSW Treasury yield curve from the Fed"""
    return {
        "actions": ["python ./src/pull_gsw.py"],
        "file_dep": ["./src/pull_gsw.py"],
        "targets": [GSW],
        "uptodate": [config_changed(SAMPLE)],
        "clean": [],
    }


def task_pull_fred():
    """Pull benchmark rate series from FRED"""
    return {
        "actions": ["python ./src/pull_fred.py"],
        "file_dep": ["./src/pull_fred.py"],
        "targets": [FRED],
        "uptodate": [config_changed(SAMPLE)],
        "clean": [],
    }


def task_pull_databento():
    """Pull CME futures daily bars, and ZQ trades around FOMC announcements"""
    return {
        "actions": ["python ./src/pull_databento.py"],
        "file_dep": ["./src/pull_databento.py", FOMC_CALENDAR],
        "targets": [FUTURES_DAILY, ZQ_EVENT_TRADES],
        "uptodate": [
            config_changed(
                {
                    **SAMPLE,
                    "DATABENTO_DATASET": DATABENTO_DATASET,
                    "FOMC_WINDOW_MINUTES": FOMC_WINDOW_MINUTES,
                }
            )
        ],
        "clean": [],
    }


def task_pull_crsp_treasury():
    """Pull CRSP Treasury daily quotes and issue information (WRDS)"""
    return {
        "actions": ["python ./src/pull_crsp_treasury.py"],
        "file_dep": ["./src/pull_crsp_treasury.py"],
        "targets": CRSP_TREASURY,
        "uptodate": [config_changed(SAMPLE)],
        "clean": [],
    }


def task_clean_options():
    """Filter the raw option quotes into matched call-put pairs"""
    return {
        "actions": ["python ./src/clean_options.py"],
        "file_dep": ["./src/clean_options.py", *OPPRCD],
        "targets": [CLEAN_OPTION_PAIRS, FILTER_FUNNEL],
        "clean": True,
    }


def task_calc_box_rates():
    """Estimate box rates by expiry, and interpolate them to fixed tenors"""
    return {
        "actions": ["python ./src/calc_box_rates.py"],
        "file_dep": ["./src/calc_box_rates.py", CLEAN_OPTION_PAIRS],
        "targets": [BOX_RATES_BY_EXPIRY, BOX_RATES_FIXED_TENOR],
        "uptodate": [config_changed({"TENORS_M": TENORS_M})],
        "clean": True,
    }


def task_calc_bidask():
    """Daily median relative bid-ask spreads, by index and option type"""
    return {
        "actions": ["python ./src/calc_bidask.py"],
        "file_dep": ["./src/calc_bidask.py", CLEAN_OPTION_PAIRS],
        "targets": [BIDASK_DAILY],
        "clean": True,
    }


def task_calc_benchmarks():
    """Benchmark rates on the box-rate tenors, in common units"""
    return {
        "actions": ["python ./src/calc_benchmarks.py"],
        "file_dep": ["./src/calc_benchmarks.py", GSW, FRED, ZEROCD, FUTURES_DAILY],
        "targets": [BENCHMARK_RATES],
        "uptodate": [config_changed({"TENORS_M": TENORS_M})],
        "clean": True,
    }


def task_calc_fomc_surprises():
    """Fed funds futures surprises for each FOMC announcement"""
    return {
        "actions": ["python ./src/calc_fomc_surprises.py"],
        "file_dep": ["./src/calc_fomc_surprises.py", FOMC_CALENDAR, ZQ_EVENT_TRADES],
        "targets": [FOMC_SURPRISES],
        "clean": True,
    }


def task_calc_treasury_arbitrage():
    """Treasury market spreads for Table 11 (CRSP and GSW)"""
    return {
        "actions": ["python ./src/calc_treasury_arbitrage.py"],
        "file_dep": ["./src/calc_treasury_arbitrage.py", *CRSP_TREASURY, GSW],
        "targets": [TREASURY_SPREADS],
        "clean": True,
    }


def task_calc_tables():
    """Write the report's tables as LaTeX files"""
    return {
        "actions": ["python ./src/calc_tables.py"],
        "file_dep": [
            "./src/calc_tables.py",
            BOX_RATES_FIXED_TENOR,
            BENCHMARK_RATES,
            BIDASK_DAILY,
            FOMC_SURPRISES,
            TREASURY_SPREADS,
            FILTER_FUNNEL,
        ],
        "targets": [*TABLES, FUNNEL_TABLE],
        "clean": True,
    }


## Notebooks to run, keyed by file name, each with "path", "file_dep" and
## "targets". Empty until the P18 notebooks exist.
notebook_tasks = {}


# fmt: off
def task_run_notebooks():
    """Preps the notebooks for presentation format.
    Execute notebooks if the script version of it has been changed.
    """
    for notebook in notebook_tasks.keys():
        pyfile_path = Path(notebook_tasks[notebook]["path"])
        notebook_path = pyfile_path.with_suffix("")  # strips .py, leaves .ipynb
        notebook_name = notebook_path.stem  # e.g. "01_example_notebook_interactive"
        yield {
            "name": notebook,
            "actions": [
                """python -c "import sys; from datetime import datetime; print(f'Start """ + notebook + """: {datetime.now()}', file=sys.stderr)" """,
                f"jupytext --to notebook --output {notebook_path} {pyfile_path}",
                jupyter_execute_notebook(notebook_path),
                jupyter_to_html(notebook_path),
                mv(notebook_path, OUTPUT_DIR),
                """python -c "import sys; from datetime import datetime; print(f'End """ + notebook + """: {datetime.now()}', file=sys.stderr)" """,
            ],
            "file_dep": [
                pyfile_path,
                *notebook_tasks[notebook]["file_dep"],
            ],
            "targets": [
                OUTPUT_DIR / f"{notebook_name}.html",
                *notebook_tasks[notebook]["targets"],
            ],
            "clean": True,
        }
# fmt: on

###############################################################
## Task below is for LaTeX compilation
###############################################################


def task_compile_latex_docs():
    """Compile the LaTeX documents to PDFs"""
    file_dep = [
        "./reports/report_example.tex",
        "./reports/my_article_header.sty",
        "./reports/slides_example.tex",
        "./reports/my_beamer_header.sty",
        "./reports/my_common_header.sty",
        "./reports/report_simple_example.tex",
        "./reports/slides_simple_example.tex",
        # Generated inputs go here (tables and charts in OUTPUT_DIR). The reports
        # typeset a placeholder for a missing one instead of failing, so list
        # them here to have doit build them first.
    ]
    targets = [
        "./reports/report_example.pdf",
        "./reports/slides_example.pdf",
        "./reports/report_simple_example.pdf",
        "./reports/slides_simple_example.pdf",
    ]

    return {
        "actions": [
            # My custom LaTeX templates
            "latexmk -xelatex -interaction=nonstopmode -halt-on-error -cd ./reports/report_example.tex",  # Compile
            "latexmk -xelatex -halt-on-error -c -cd ./reports/report_example.tex",  # Clean
            "latexmk -xelatex -interaction=nonstopmode -halt-on-error -cd ./reports/slides_example.tex",  # Compile
            "latexmk -xelatex -halt-on-error -c -cd ./reports/slides_example.tex",  # Clean
            # Simple templates based on small adjustments to Overleaf templates
            "latexmk -xelatex -interaction=nonstopmode -halt-on-error -cd ./reports/report_simple_example.tex",  # Compile
            "latexmk -xelatex -halt-on-error -c -cd ./reports/report_simple_example.tex",  # Clean
            "latexmk -xelatex -interaction=nonstopmode -halt-on-error -cd ./reports/slides_simple_example.tex",  # Compile
            "latexmk -xelatex -halt-on-error -c -cd ./reports/slides_simple_example.tex",  # Clean
        ],
        "targets": targets,
        "file_dep": file_dep,
        "clean": True,
    }

sphinx_targets = [
    "./docs/index.html",
]


def task_build_chartbook_site():
    """Compile Sphinx Docs"""
    notebook_scripts = [
        Path(notebook_tasks[notebook]["path"])
        for notebook in notebook_tasks.keys()
    ]
    file_dep = [
        "./README.md",
        "./chartbook.toml",
        *notebook_scripts,
    ]

    return {
        "actions": [
            "chartbook docs build -f",
        ],  # Use docs as build destination
        "targets": sphinx_targets,
        "file_dep": file_dep,
        "task_dep": [
            "run_notebooks",
        ],
        "clean": True,
    }


def task_run_pytest():
    """Run pytest and save results to OUTPUT_DIR"""
    src_py_files = list(Path("./src").glob("*.py"))
    test_output = OUTPUT_DIR / "pytest_results.xml"

    def run_pytest():
        import subprocess

        result = subprocess.run(
            ["pytest", f"--junitxml={test_output}"],
        )
        if result.returncode != 0:
            # Remove the XML so doit won't consider the target up-to-date
            Path(test_output).unlink(missing_ok=True)
            raise RuntimeError(f"pytest failed with exit code {result.returncode}")

    return {
        "actions": [run_pytest],
        "targets": [test_output],
        "file_dep": src_py_files,
        "clean": True,
        "verbosity": 2,
    }
