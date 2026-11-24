"""Tests for calc_benchmarks, on synthetic inputs. No data, no network.

Each unit conversion is checked by a round trip: start from a known
continuously compounded rate r, write it in the quoting convention by hand,
and check that the conversion returns r.
"""

import numpy as np
import pandas as pd
import pytest

from calc_benchmarks import (
    COLUMNS,
    bond_equivalent_to_cc,
    build_benchmarks,
    cmt_rates,
    discount_yield_to_cc,
    gsw_rates,
    interp_no_extrapolation,
    load_bloomberg,
    overnight_rates,
    simple_act360_to_cc,
    svensson_spot,
    tbill_rates,
    tenor_days,
    zerocd_rates,
)

R = 0.03  # the known continuous rate of the round trips
DATES = pd.to_datetime(["2020-01-02", "2020-01-03"])


def test_tenor_days_is_act365():
    assert tenor_days(12) == pytest.approx(365)
    assert tenor_days(3) == pytest.approx(91.25)


## Conversions


def test_svensson_flat_curve():
    """With every slope and curvature at zero, the curve is flat at BETA0."""
    y = svensson_spot([0.25, 1, 10], 4.0, 0.0, 0.0, 0.0, 1.0, 10.0)
    assert np.allclose(y, 4.0)


def test_svensson_by_hand():
    """t = tau1 = 1, only BETA1: y = BETA0 + BETA1 (1 - e^-1)."""
    y = svensson_spot(1.0, 4.0, -1.0, 0.0, 0.0, 1.0, 10.0)
    assert y == pytest.approx(4.0 - (1 - np.exp(-1)), abs=1e-12)


def test_svensson_ignores_tau2_when_beta3_is_zero():
    y = svensson_spot(1.0, 4.0, -1.0, 0.5, 0.0, 1.0, np.nan)
    assert np.isfinite(y)


@pytest.mark.parametrize("n_days", [91, 182, 364])
def test_discount_yield_round_trip(n_days):
    price = np.exp(-R * n_days / 365)
    d_pct = (1 - price) * 360 / n_days * 100
    assert discount_yield_to_cc(d_pct, n_days) == pytest.approx(R, abs=1e-12)


def test_bond_equivalent_round_trip():
    y_pct = 2 * (np.exp(R / 2) - 1) * 100
    assert bond_equivalent_to_cc(y_pct) == pytest.approx(R, abs=1e-12)


@pytest.mark.parametrize("n_days", [1, 91.25, 365])
def test_simple_act360_round_trip(n_days):
    rate_pct = (np.exp(R * n_days / 365) - 1) * 360 / n_days * 100
    assert simple_act360_to_cc(rate_pct, n_days) == pytest.approx(R, abs=1e-12)


def test_interp_never_extrapolates_and_skips_nan():
    out = interp_no_extrapolation([5, 15, 25, 35], [10, 20, 30], [1.0, np.nan, 3.0])
    assert np.isnan(out[0]) and np.isnan(out[3])  # outside [10, 30]
    assert out[1] == pytest.approx(1.5) and out[2] == pytest.approx(2.5)


def test_interp_needs_two_points():
    assert np.isnan(interp_no_extrapolation([1.0], [1.0], [2.0])).all()


## Sources


def test_gsw_rates_flat_curve_in_decimals():
    gsw = pd.DataFrame(
        {
            "date": DATES,
            "BETA0": 3.0,
            "BETA1": 0.0,
            "BETA2": 0.0,
            "BETA3": 0.0,
            "TAU1": 1.0,
            "TAU2": 10.0,
        }
    )
    out = gsw_rates(gsw, tenors=(3, 18))
    assert list(out.columns) == COLUMNS
    assert set(out["tenor_m"]) == {3, 18}
    assert np.allclose(out["rate"], 0.03)


def test_zerocd_rates_interpolate_and_stop_at_curve_end():
    zerocd = pd.DataFrame(
        {"date": DATES[0], "days": [30, 200, 400], "rate": [2.0, 3.0, 4.0]}
    )
    out = zerocd_rates(zerocd, tenors=(3, 12, 18)).set_index("tenor_m")["rate"]
    # 3m = 91.25 days, between 30 and 200: 2 + (91.25 - 30) / 170 percent
    assert out[3] == pytest.approx((2.0 + 61.25 / 170) / 100)
    assert out[12] == pytest.approx((3.0 + 165 / 200) / 100)  # 365 days
    assert 18 not in out.index  # 547.5 days > 400: no extrapolation


def test_tbill_rates():
    d_pct = {
        m: (1 - np.exp(-R * n / 365)) * 360 / n * 100
        for m, n in [(3, 91), (6, 182), (12, 364)]
    }
    fred = pd.DataFrame(
        {"date": DATES, "DTB3": d_pct[3], "DTB6": d_pct[6], "DTB1YR": np.nan}
    )
    out = tbill_rates(fred)
    assert set(out["tenor_m"]) == {3, 6}  # the missing 1-year bill is left out
    assert np.allclose(out["rate"], R)


def test_cmt_rates_flat():
    y_pct = 2 * (np.exp(R / 2) - 1) * 100
    codes = ["DGS1MO", "DGS3MO", "DGS6MO", "DGS1", "DGS2", "DGS3"]
    fred = pd.DataFrame({"date": DATES, **{c: y_pct for c in codes}})
    out = cmt_rates(fred, tenors=(3, 18, 30))
    assert len(out) == 6
    assert np.allclose(out["rate"], R)


def test_overnight_rates_keep_sofr_gaps():
    s_pct = (np.exp(R / 365) - 1) * 360 * 100
    fred = pd.DataFrame({"date": DATES, "SOFR": [np.nan, s_pct], "EFFR": s_pct})
    out = overnight_rates(fred)
    assert set(out["tenor_m"]) == {0}
    assert (out["source"] == "sofr").sum() == 1  # the NaN day is dropped
    assert np.allclose(out["rate"], R)


def test_load_bloomberg_missing_file_returns_none(tmp_path, capsys):
    assert load_bloomberg("ois_bbg", manual_dir=tmp_path) is None
    assert "left out" in capsys.readouterr().out


def test_load_bloomberg_converts(tmp_path):
    rate_pct = (np.exp(R * 91.25 / 365) - 1) * 360 / 91.25 * 100
    pd.DataFrame({"date": ["2010-01-04"], "tenor_m": [3], "rate": [rate_pct]}).to_csv(
        tmp_path / "bloomberg_gc_repo.csv", index=False
    )
    out = load_bloomberg("gc_repo", manual_dir=tmp_path)
    assert list(out.columns) == COLUMNS
    assert out["rate"].iloc[0] == pytest.approx(R, abs=1e-12)


def test_build_benchmarks_stacks_every_source(tmp_path):
    gsw = pd.DataFrame(
        {
            "date": DATES,
            **{"BETA0": 3.0, "BETA1": 0.0, "BETA2": 0.0, "BETA3": 0.0},
            **{"TAU1": 1.0, "TAU2": 10.0},
        }
    )
    codes = ["DTB3", "DTB6", "DTB1YR", "DGS1MO", "DGS3MO", "DGS6MO", "DGS1", "DGS2"]
    fred = pd.DataFrame(
        {
            "date": DATES,
            "SOFR": 3.0,
            "EFFR": 3.0,
            "DGS3": 3.0,
            **{c: 3.0 for c in codes},
        }
    )
    zerocd = pd.DataFrame({"date": DATES[0], "days": [10, 1000], "rate": 3.0})
    out = build_benchmarks(gsw, fred, zerocd, manual_dir=tmp_path)
    assert list(out.columns) == COLUMNS
    assert set(out["source"]) == {"gsw", "libor_om", "tbill", "cmt", "sofr", "effr"}
    assert not out.duplicated(["date", "source", "tenor_m"]).any()
    assert out["rate"].between(0, 0.05).all()  # decimals, not percent
