"""Load project configurations from .env files or from the command line.

Provides easy access to paths and credentials used in the project.
Meant to be used as an imported module.

If `settings.py` is run on its own, it will create the appropriate
directories.

For information about the rationale behind decouple and this module,
see https://pypi.org/project/python-decouple/

Note that decouple mentions that it will help to ensure that
the project has "only one configuration module to rule all your instances."
This is achieved by putting all the configuration into the `.env` file.
You can have different sets of variables for difference instances,
such as `.env.development` or `.env.production`. You would only
need to copy over the settings from one into `.env` to switch
over to the other configuration, for example.


Example
-------
Create a file called `myexample.py` with the following content:
```
from settings import config
DATA_DIR = config("DATA_DIR")

print(f"Using DATA_DIR: {DATA_DIR}")
```
and run
```
>>> python myexample.py --DATA_DIR=/path/to/data
/path/to/data
```
and compare to
```
>>> export DATA_DIR=/path/to/other
>>> python myexample.py
/path/to/other
```

"""

import sys
from pathlib import Path
from platform import system

from decouple import config as _config


def find_all_caps_cli_vars(argv=sys.argv):
    """Find all command line arguments that are all caps.

    Find all command line arguments that are all caps and defined
    with a long option, for example, --DATA_DIR or --MANUAL_DATA_DIR.
    When that option is found, the value of the option is returned.

    For example, if the command line is:
    ```
    python settings.py --DATA_DIR=/path/to/data --MANUAL_DATA_DIR=/path/to/manual_data
    ```
    Then the function will return:
    ```
    {'DATA_DIR': '/path/to/data', 'MANUAL_DATA_DIR': '/path/to/manual_data'}
    ```

    For example:
    ```
    >>> argv = [
        '/opt/homebrew/Caskroom/mambaforge/base/envs/ftsf/lib/python3.12/site-packages/ipykernel_launcher.py',
        '--f=/Users/jbejarano/Library/Jupyter/runtime/kernel-v37ea18e94713e364855d5610175b766ee99909eab.json',
        '--DATA_DIR=/path/to/data',
        '--MANUAL_DATA_DIR=/path/to/manual_data'
    ]
    >>> cli_vars = find_all_caps_cli_vars(argv)
    >>> cli_vars
    {'DATA_DIR': '/path/to/data', 'MANUAL_DATA_DIR': '/path/to/manual_data'}
    ```
    """
    result = {}
    i = 0
    while i < len(argv):
        arg = argv[i]
        # Handle --VAR=value format
        if arg.startswith("--") and "=" in arg and arg[2:].split("=")[0].isupper():
            var_name, value = arg[2:].split("=", 1)
            result[var_name] = value
        # Handle --VAR value format (where value is the next argument)
        elif arg.startswith("--") and arg[2:].isupper() and i + 1 < len(argv):
            var_name = arg[2:]
            value = argv[i + 1]
            # Only use this value if it doesn't look like another option
            if not value.startswith("--"):
                result[var_name] = value
                i += 1  # Skip the next argument since we used it as a value
        i += 1
    return result


cli_vars = find_all_caps_cli_vars()

########################################################
## Define defaults
########################################################
defaults = {}

# Absolute path to root directory of the project
if "BASE_DIR" in cli_vars:
    defaults["BASE_DIR"] = Path(cli_vars["BASE_DIR"])
else:
    defaults["BASE_DIR"] = Path(__file__).absolute().parent.parent


# OS type
def get_os():
    os_name = system()
    if os_name == "Windows":
        return "windows"
    elif os_name == "Darwin":
        return "nix"
    elif os_name == "Linux":
        return "nix"
    else:
        return "unknown"


if "OS_TYPE" in cli_vars:
    defaults["OS_TYPE"] = cli_vars["OS_TYPE"]
else:
    defaults["OS_TYPE"] = get_os()


## Stata executable
def get_stata_exe():
    """Get the name of the Stata executable based on the OS type."""
    if defaults["OS_TYPE"] == "windows":
        return "StataMP-64.exe"
    elif defaults["OS_TYPE"] == "nix":
        return "stata-mp"
    else:
        raise ValueError("Unknown OS type")


if "STATA_EXE" in cli_vars:
    defaults["STATA_EXE"] = cli_vars["STATA_EXE"]
else:
    defaults["STATA_EXE"] = get_stata_exe()

########################################################
## Committed constants
########################################################
## These change what the pipeline computes, so they live in this committed file
## and never in .env: two people who build the same commit must get the same
## bytes. `.env` holds only secrets and machine-specific paths (WRDS_USERNAME,
## DATABENTO_API_KEY, DATA_DIR). Import the constants directly, e.g.
## `from settings import END_DATE`. `config()` refuses them, and importing this
## module raises if .env, the environment or the command line tries to set one.

## Sample period: ISO dates, inclusive.
START_DATE = "2004-01-01"  # start of the paper's sample
REPLICATION_END = "2018-12-31"  # end of the paper's sample (NBER WP 26138)
## END_DATE is the last date of OptionMetrics on WRDS: optionm_all.opprcd2025
## ends on 2025-08-29 for both SPX and DJX (checked 2026-11-23; there is no
## opprcd2026 yet). Moving it takes a commit, and it reruns every pull.
END_DATE = "2025-08-29"

## OptionMetrics security IDs (optionm_all.securd, cross-checked in secnmd).
SPX_SECID = 108105  # S&P 500 index
DJX_SECID = 102456  # Dow Jones Industrial Average index (1/100 of the DJIA)

## Fixed maturities of the box-rate panels, in months.
TENORS_M = (3, 6, 12, 18, 30)

## Databento: CME Globex, for the fed funds, SOFR and Treasury futures.
DATABENTO_DATASET = "GLBX.MDP3"
## Half-width of the intraday window pulled around each FOMC announcement:
## from 120 minutes before it to 120 minutes after.
FOMC_WINDOW_MINUTES = 120

COMMITTED_CONSTANTS = (
    "START_DATE",
    "REPLICATION_END",
    "END_DATE",
    "SPX_SECID",
    "DJX_SECID",
    "TENORS_M",
    "DATABENTO_DATASET",
    "FOMC_WINDOW_MINUTES",
)


## File paths
def if_relative_make_abs(path):
    """If a relative path is given, make it absolute, assuming
    that it is relative to the project root directory (BASE_DIR)

    Example
    -------
    ```
    >>> if_relative_make_abs(Path('_data'))
    WindowsPath('C:/Users/jdoe/repos/p18/_data')

    >>> if_relative_make_abs(Path("C:/Users/jdoe/repos/p18/_output"))
    WindowsPath('C:/Users/jdoe/repos/p18/_output')
    ```
    """
    path = Path(path)
    if path.is_absolute():
        abs_path = path.resolve()
    else:
        abs_path = (defaults["BASE_DIR"] / path).resolve()
    return abs_path


defaults = {
    "DATA_DIR": if_relative_make_abs(Path("_data")),
    "MANUAL_DATA_DIR": if_relative_make_abs(Path("data_manual")),
    "OUTPUT_DIR": if_relative_make_abs(Path("_output")),
    **defaults,
}


def config(
    var_name,
    default=None,
    cast=None,
    settings_py_defaults=defaults,
    cli_vars=cli_vars,
    convert_dir_vars_to_abs_path=True,
):
    """Config defines a variable that can be used in the project. The definition of
    variables follows an order of precedence:
    1. Command line arguments
    2. Environment variables
    3. Settings.py file
    4. Defaults defined in-line in the local file
    5. Error

    The committed constants (COMMITTED_CONSTANTS) are not settings and are
    refused here: import them from this module instead.
    """
    if var_name in COMMITTED_CONSTANTS:
        raise ValueError(
            f"{var_name} is a committed constant in settings.py, not a setting: "
            f"use `from settings import {var_name}`. It is never read from .env, "
            "the environment or the command line."
        )

    # 1. Command line arguments (highest priority)
    if var_name in cli_vars and cli_vars[var_name] is not None:
        value = cli_vars[var_name]
        # Apply cast if provided
        if cast is not None:
            value = cast(value)
        if "DIR" in var_name and convert_dir_vars_to_abs_path:
            value = if_relative_make_abs(Path(value))
        return value

    # 2. Environment variables through decouple
    # Use decouple but with a sentinel default to detect if it was found
    env_sentinel = object()
    env_value = _config(var_name, default=env_sentinel)
    if env_value is not env_sentinel:
        # Found in environment
        if cast is not None:
            env_value = cast(env_value)
        if "DIR" in var_name and convert_dir_vars_to_abs_path:
            env_value = if_relative_make_abs(Path(env_value))
        return env_value

    # 3. Settings.py defaults dictionary
    if var_name in defaults:
        default_value = defaults[var_name]
        # If default_value is directly usable (not a dict with metadata)
        if cast is not None:
            default_value = cast(default_value)
        return default_value

    # 4. Use the default value provided in the local file. Error if not found
    try:
        return _config(var_name, default=default, cast=cast)
    except Exception as e:
        raise ValueError(
            f"Configuration variable '{var_name}' is not defined. "
            f"Please set it via:\n"
            f"  1. Command line: --{var_name}=value\n"
            f"  2. Environment variable: export {var_name}=value\n"
            f"  3. .env file: {var_name}=value\n"
            f"Original error: {e}"
        ) from e


def check_no_overrides(names=COMMITTED_CONSTANTS, cli_vars=cli_vars):
    """Raise if .env, the environment or the command line sets a committed constant.

    Without this check, a line such as END_DATE=2026-12-31 in someone's .env
    would be silently ignored, and they would think the pipeline used it.
    """
    sentinel = object()
    found = [
        name
        for name in names
        if name in cli_vars or _config(name, default=sentinel) is not sentinel
    ]
    if found:
        raise ValueError(
            f"{', '.join(found)} is set in .env, the environment or the command "
            "line. These are committed constants in src/settings.py: remove them "
            "there, and change them in settings.py, by commit, if needed."
        )


check_no_overrides()


def create_directories():
    config("DATA_DIR").mkdir(parents=True, exist_ok=True)
    config("OUTPUT_DIR").mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    create_directories()
