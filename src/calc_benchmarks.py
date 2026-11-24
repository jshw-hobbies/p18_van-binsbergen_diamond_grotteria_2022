"""Build the benchmark rates the box rates are compared with, on the same tenors.

Domain B (benchmark rates). Stage: calc.

Inputs
------
- ``DATA_DIR/gsw_yield_curve.parquet`` (``pull_gsw``), ``fred.parquet``
  (``pull_fred``) and ``optionm_zerocd.parquet`` (``pull_zerocd``).
- Optional Bloomberg exports in ``DATA_DIR/manual/`` (see "Bloomberg files"
  below). If one is missing, a message is printed and its rows are left out, so
  the tables show n/a. Raw Bloomberg data never goes into git.

Output
------
``DATA_DIR/benchmark_rates.parquet`` (long). Grain: date x source x tenor_m.
Columns: ``date, source, tenor_m, rate``. Every ``rate`` is a decimal,
continuously compounded, with maturities on ACT/365. A tenor of m months is
``m * 365 / 12`` days, or ``m / 12`` years. Overnight rates have ``tenor_m = 0``.

========= =============================== ===================== =================
source    Input                           Tenors (months)       Dates
========= =============================== ===================== =================
gsw       GSW Svensson parameters         every ``TENORS_M``    2004 on
libor_om  OptionMetrics ``zerocd``        every ``TENORS_M``    2004 on
tbill     FRED DTB3, DTB6, DTB1YR         3, 6, 12              12m from 2008-06
cmt       FRED DGS1MO ... DGS3            every ``TENORS_M``    2004 on
sofr      FRED SOFR                       0 (overnight)         2018-04 on
effr      FRED EFFR                       0 (overnight)         2004 on
ois_bbg   Bloomberg export (optional)     as exported
gc_repo   Bloomberg export (optional)     as exported
========= =============================== ===================== =================

``cmt`` is only a cross-check of ``gsw``: the two should agree within a few
basis points (``print_validation``).

Conversions
-----------
- **GSW**: ``y(t)`` from the Svensson formula (``svensson_spot``), with the
  Fed's ``BETA0``-``BETA3`` in percent and ``TAU1``, ``TAU2`` in years; divide by
  100. GSW yields are already continuously compounded. The Fed publishes
  ``SVENYxx`` at whole years only, hence the formula for 3, 6, 18 and 30 months.
- **zerocd**: continuously compounded, in percent, against calendar days. On
  each date, interpolate linearly in days to ``m * 365 / 12``; never
  extrapolate beyond the curve's shortest or longest maturity.
- **T-bills** are quoted on a discount basis: price ``P = 1 - d n / 360`` for
  ``n`` days to maturity, so ``r = -(365 / n) ln P``. ``n`` is the bill's
  nominal maturity: 91, 182 and 364 days for the 3-, 6- and 12-month bills,
  which are stored at ``tenor_m`` 3, 6 and 12.
- **Constant-maturity Treasuries** are bond-equivalent yields (semiannual
  compounding): ``r = 2 ln(1 + y / 2)``. Then linear interpolation in maturity
  across 1, 3, 6, 12, 24 and 36 months, without extrapolation.
- **Overnight rates** (SOFR, EFFR) are simple, ACT/360, for one day:
  ``r = 365 ln(1 + s / 360)``.
- **LIBOR and money-market quotes** (Bloomberg OIS up to 12 months, GC repo)
  are simple, ACT/360: ``r = (365 / d) ln(1 + L d / 360)`` with
  ``d = m * 365 / 12``. OIS beyond 12 months pays annually, so this formula is
  only an approximation there.

Bloomberg files
---------------
Optional, gitignored, in ``DATA_DIR/manual/``:

- ``bloomberg_ois.csv`` and ``bloomberg_gc_repo.csv``, each with columns
  ``date, tenor_m, rate``: ``rate`` in percent, as Bloomberg quotes it (simple,
  ACT/360). Adjust ``load_bloomberg`` if the lab's export looks different.

Futures-implied rates
---------------------
The formulas are built and tested (``chain_forwards`` and its helpers). Wiring
them to data waits for ``pull_databento`` (domain C) to fix the columns of
``futures_daily.parquet``; ``FUTURES_DAILY`` joins this task's ``file_dep``
then, and the sources ``zq_implied``, ``sofr_fut_implied`` and ``ge_implied``
join the output.

Every contract implies a continuously compounded forward rate over a span of
days:

- **averaging contracts**, ``ZQ`` (fed funds) and ``SR1`` (1-month SOFR): the
  price ``P`` of the contract for a calendar month implies the month's average
  overnight rate ``f = 100 - P`` (percent, simple, ACT/360). Compounded daily,
  that is the forward ``365 ln(1 + f / 360)`` over the month
  (``month_segment``);
- **period contracts**, ``SR3`` (3-month SOFR, compounded over its IMM reference
  quarter) and ``GE`` (Eurodollar, 3-month LIBOR from its IMM date): ``R = 100 -
  P`` is a simple ACT/360 rate over the quarter's ``N`` days, so the forward is
  ``(365 / N) ln(1 + R N / 360)`` (``quarter_segment``). The quarter runs from
  the third Wednesday of the contract month (``imm_date``) to the third
  Wednesday three months later.

The term rate from the quote date ``q`` over ``H`` days is the day-weighted
average of the forwards covering ``[q, q + H)`` (``chain_forwards``), which is
NaN if the segments leave a gap: no extrapolation. A 3-month SOFR rate chains
SR1 months up to the first SR3 quarter, then SR3 quarters.

Approximations, to state wherever these rates are used:

- futures are not swaps: they carry a convexity bias (small at these
  horizons), which is ignored;
- in the current month, the contract's average includes days already past;
  the formula applies the month's average to the remaining days too;
- ``GE`` implies LIBOR, which has credit risk: compare it with ``libor_om``,
  not with the risk-free rates.

Reuse: the course's ``fed_yield_curve`` repo, ``src/gsw_pricing.py``
(``svensson_spot``, here taking the Fed's columns directly).
"""

from pathlib import Path

import numpy as np
import pandas as pd

from settings import TENORS_M, config

DATA_DIR = config("DATA_DIR")
MANUAL_DIR = DATA_DIR / "manual"
OUTPUT_FILE = "benchmark_rates.parquet"

COLUMNS = ["date", "source", "tenor_m", "rate"]

TBILLS = {3: ("DTB3", 91), 6: ("DTB6", 182), 12: ("DTB1YR", 364)}
CMT_MONTHS = {
    "DGS1MO": 1,
    "DGS3MO": 3,
    "DGS6MO": 6,
    "DGS1": 12,
    "DGS2": 24,
    "DGS3": 36,
}
OVERNIGHT = {"sofr": "SOFR", "effr": "EFFR"}
BLOOMBERG = {"ois_bbg": "bloomberg_ois.csv", "gc_repo": "bloomberg_gc_repo.csv"}


def tenor_days(tenor_m):
    """Days in a tenor of ``tenor_m`` months, on ACT/365: ``m * 365 / 12``."""
    return np.asarray(tenor_m, dtype=float) * 365 / 12


## Unit conversions: inputs in percent, outputs decimal and continuously
## compounded on ACT/365.


def svensson_spot(t, beta0, beta1, beta2, beta3, tau1, tau2):
    """Svensson zero yield at maturity ``t`` years, in the units of the betas.

    Takes the Fed's GSW parameters directly (betas in percent, taus in years)
    and broadcasts over arrays. When ``beta3`` is 0 (Nelson-Siegel days), its
    term is 0 whatever ``tau2`` is.
    """
    t = np.asarray(t, dtype=float)
    x1 = t / tau1
    x2 = t / tau2
    slope1 = (1 - np.exp(-x1)) / x1
    slope2 = (1 - np.exp(-x2)) / x2
    term3 = np.where(beta3 == 0, 0.0, beta3 * (slope2 - np.exp(-x2)))
    return beta0 + beta1 * slope1 + beta2 * (slope1 - np.exp(-x1)) + term3


def discount_yield_to_cc(d_pct, n_days):
    """T-bill discount yield (percent) for ``n_days`` to a continuous ACT/365 rate."""
    price = 1 - np.asarray(d_pct, dtype=float) / 100 * n_days / 360
    return -np.log(price) * 365 / n_days


def bond_equivalent_to_cc(y_pct):
    """Bond-equivalent (semiannual) yield in percent to a continuous rate."""
    return 2 * np.log1p(np.asarray(y_pct, dtype=float) / 100 / 2)


def simple_act360_to_cc(rate_pct, n_days):
    """Simple ACT/360 rate in percent over ``n_days`` to a continuous ACT/365 rate."""
    return np.log1p(np.asarray(rate_pct, dtype=float) / 100 * n_days / 360) * (
        365 / n_days
    )


def interp_no_extrapolation(x, xp, fp):
    """``np.interp`` that returns NaN outside ``[min(xp), max(xp)]``.

    ``xp`` must be increasing. NaNs in ``fp`` are dropped first.
    """
    xp = np.asarray(xp, dtype=float)
    fp = np.asarray(fp, dtype=float)
    keep = ~np.isnan(fp)
    xp, fp = xp[keep], fp[keep]
    x = np.asarray(x, dtype=float)
    if len(xp) < 2:
        return np.full(x.shape, np.nan)
    out = np.interp(x, xp, fp)
    return np.where((x < xp[0]) | (x > xp[-1]), np.nan, out)


## One function per source. Each returns a long frame with COLUMNS.


def _long(df, source):
    """Melt a wide frame (``date`` plus one column per tenor_m) into COLUMNS."""
    out = df.melt(id_vars="date", var_name="tenor_m", value_name="rate")
    out["source"] = source
    out["tenor_m"] = out["tenor_m"].astype("int64")
    return out.dropna(subset=["rate"])[COLUMNS]


def gsw_rates(gsw, tenors=TENORS_M):
    """GSW zero yields at ``tenors`` months, from the Svensson parameters."""
    params = [gsw[c].to_numpy() for c in ("BETA0", "BETA1", "BETA2", "BETA3")]
    taus = [gsw[c].to_numpy() for c in ("TAU1", "TAU2")]
    wide = pd.DataFrame({"date": gsw["date"]})
    for m in tenors:
        wide[m] = svensson_spot(m / 12, *params, *taus) / 100
    return _long(wide, "gsw")


def zerocd_rates(zerocd, tenors=TENORS_M):
    """OptionMetrics zero rates at ``tenors`` months, interpolated in days per date."""
    targets = tenor_days(tenors)
    rows = []
    for date, curve in zerocd.sort_values(["date", "days"]).groupby("date"):
        rates = interp_no_extrapolation(targets, curve["days"], curve["rate"])
        rows.append([date, *(rates / 100)])
    wide = pd.DataFrame(rows, columns=["date", *tenors])
    return _long(wide, "libor_om")


def tbill_rates(fred):
    """T-bill rates at 3, 6 and 12 months, from FRED's discount yields."""
    wide = pd.DataFrame({"date": fred["date"]})
    for m, (code, n_days) in TBILLS.items():
        wide[m] = discount_yield_to_cc(fred[code], n_days)
    return _long(wide, "tbill")


def cmt_rates(fred, tenors=TENORS_M):
    """Constant-maturity Treasury yields at ``tenors`` months, interpolated per date."""
    months = np.array(list(CMT_MONTHS.values()), dtype=float)
    cc = bond_equivalent_to_cc(fred[list(CMT_MONTHS)].to_numpy())
    rates = np.array([interp_no_extrapolation(tenors, months, row) for row in cc])
    wide = pd.DataFrame(rates, columns=list(tenors))
    wide.insert(0, "date", fred["date"].to_numpy())
    return _long(wide, "cmt")


def overnight_rates(fred):
    """SOFR and EFFR as one-day continuous rates, at ``tenor_m = 0``."""
    frames = []
    for source, code in OVERNIGHT.items():
        wide = pd.DataFrame(
            {"date": fred["date"], 0: simple_act360_to_cc(fred[code], 1)}
        )
        frames.append(_long(wide, source))
    return pd.concat(frames, ignore_index=True)


def load_bloomberg(source, manual_dir=MANUAL_DIR):
    """An optional Bloomberg export as COLUMNS, or None (with a message) if absent.

    The file has ``date, tenor_m, rate``, with ``rate`` in percent, simple ACT/360.
    """
    path = Path(manual_dir) / BLOOMBERG[source]
    if not path.exists():
        print(f"{source}: no {path}, so its rows are left out (tables show n/a)")
        return None
    raw = pd.read_csv(path, parse_dates=["date"])
    out = raw[["date", "tenor_m"]].copy()
    out["tenor_m"] = out["tenor_m"].astype("int64")
    out["rate"] = simple_act360_to_cc(raw["rate"], tenor_days(out["tenor_m"]))
    out["source"] = source
    return out.dropna(subset=["rate"])[COLUMNS]


## Futures-implied rates: formulas only, until futures_daily exists.


def imm_date(year, month):
    """The third Wednesday of ``month``: where SR3 and GE reference quarters start."""
    first = pd.Timestamp(year=year, month=month, day=1)
    first_wednesday = first + pd.Timedelta(days=(2 - first.weekday()) % 7)
    return first_wednesday + pd.Timedelta(weeks=2)


def month_segment(month_start, price):
    """Forward segment for an averaging contract (ZQ, SR1) on one calendar month.

    Returns ``(start, end, fwd_cc)``: the month as ``[start, end)`` and the
    continuous forward ``365 ln(1 + f / 360)``, ``f = 100 - price`` in percent.
    """
    start = pd.Timestamp(month_start).replace(day=1)
    end = start + pd.offsets.MonthBegin(1)
    return start, end, float(simple_act360_to_cc(100 - price, 1))


def quarter_segment(year, month, price):
    """Forward segment for a period contract (SR3, GE) with contract month ``month``.

    Returns ``(start, end, fwd_cc)``: the IMM quarter ``[imm(m), imm(m + 3))``
    and the continuous forward ``(365 / N) ln(1 + R N / 360)``, ``R = 100 -
    price`` in percent and ``N`` the quarter's days.
    """
    start = imm_date(year, month)
    later = pd.Timestamp(year=year, month=month, day=1) + pd.DateOffset(months=3)
    end = imm_date(later.year, later.month)
    n_days = (end - start).days
    return start, end, float(simple_act360_to_cc(100 - price, n_days))


def chain_forwards(quote_date, horizon_days, segments):
    """Term rate over ``[quote_date, quote_date + horizon_days)`` from forward segments.

    ``segments`` is a list of ``(start, end, fwd_cc)`` that must not overlap.
    The result is the day-weighted average of the forwards, a continuous rate
    on ACT/365, or NaN if the segments do not cover every day of the horizon.
    """
    q = pd.Timestamp(quote_date)
    h_end = q + pd.Timedelta(days=horizon_days)
    covered, weighted = 0, 0.0
    for start, end, fwd in sorted(segments, key=lambda seg: seg[0]):
        days = (min(end, h_end) - max(start, q)).days
        if days > 0:
            covered += days
            weighted += days * fwd
    if covered > horizon_days:
        raise ValueError("Forward segments overlap")
    return weighted / horizon_days if covered == horizon_days else np.nan


def build_benchmarks(gsw, fred, zerocd, manual_dir=MANUAL_DIR, tenors=TENORS_M):
    """Every benchmark source, stacked into one long frame with COLUMNS."""
    frames = [
        gsw_rates(gsw, tenors),
        zerocd_rates(zerocd, tenors),
        tbill_rates(fred),
        cmt_rates(fred, tenors),
        overnight_rates(fred),
    ]
    for source in BLOOMBERG:
        frame = load_bloomberg(source, manual_dir)
        if frame is not None:
            frames.append(frame)
    out = pd.concat(frames, ignore_index=True)
    return out.sort_values(["source", "tenor_m", "date"]).reset_index(drop=True)


def print_validation(bench):
    """Print the mean and max absolute GSW - CMT gap, in basis points, by tenor."""
    wide = bench[bench["source"].isin(["gsw", "cmt"])].pivot_table(
        index=["date", "tenor_m"], columns="source", values="rate"
    )
    gap = ((wide["gsw"] - wide["cmt"]).abs() * 1e4).groupby("tenor_m")
    print("GSW vs CMT, absolute gap in bp:")
    print(gap.agg(["mean", "max", "count"]).round(1).to_string())


def load_benchmarks(data_dir=DATA_DIR):
    """Load ``benchmark_rates.parquet`` from ``data_dir``."""
    return pd.read_parquet(Path(data_dir) / OUTPUT_FILE)


if __name__ == "__main__":
    from pull_fred import load_fred
    from pull_gsw import load_gsw
    from pull_zerocd import load_zerocd

    bench = build_benchmarks(load_gsw(), load_fred(), load_zerocd())
    bench.to_parquet(DATA_DIR / OUTPUT_FILE, index=False)
    print(f"benchmarks: wrote {len(bench)} rows to {DATA_DIR / OUTPUT_FILE}")
    print(bench.groupby(["source", "tenor_m"])["rate"].describe().round(4))
    print_validation(bench)
