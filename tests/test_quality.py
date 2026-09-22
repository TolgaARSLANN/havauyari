import numpy as np
import pandas as pd

from havauyari.data.quality import flatline_runs, out_of_range, pm25_gt_pm10, spikes


def _idx(n):
    return pd.date_range("2024-01-01", periods=n, freq="h")


def test_pm25_gt_pm10():
    df = pd.DataFrame({"pm2_5": [5, 10, 20], "pm10": [8, 10, 15]}, index=_idx(3))
    assert pm25_gt_pm10(df) == 1


def test_flatline_runs():
    s = pd.Series([1, 1, 1, 1, 1, 1, 2, 3, 3, 3], index=_idx(10), dtype=float)
    assert flatline_runs(s, min_hours=6) == (1, 6)
    assert flatline_runs(s, min_hours=7) == (0, 6)


def test_out_of_range():
    df = pd.DataFrame({"relative_humidity_2m": [50, 101, -1], "pm2_5": [1, 2, 3]}, index=_idx(3))
    res = out_of_range(df)
    assert res["relative_humidity_2m"] == 2
    assert res["pm2_5"] == 0


def test_spikes_detects_single_outlier():
    rng = np.random.default_rng(0)
    s = pd.Series(10 + rng.normal(0, 1, 500), index=_idx(500))
    s.iloc[250] = 60
    assert spikes(s, window=48) >= 1
    assert spikes(s.drop(s.index[250]), window=48) == 0
