import numpy as np
import pandas as pd

from havauyari.data.stations import clean_station, flatline_mask, spike_mask


def _sim(pm25, pm10=None):
    idx = pd.date_range("2025-01-01", periods=len(pm25), freq="h")
    return pd.DataFrame({"PM25": pm25, "PM10": pm10 if pm10 is not None else [200.0] * len(pm25)},
                        index=idx)


def test_flatline_mask_marks_whole_run():
    s = pd.Series([1.0, 5, 5, 5, 5, 5, 5, 2, 5, 5], index=pd.RangeIndex(10))
    assert flatline_mask(s, 6).tolist() == [False] + [True] * 6 + [False] * 3


def test_flatline_ignores_nan_runs():
    s = pd.Series([np.nan] * 8 + [1.0, 2.0])
    assert not flatline_mask(s, 6).any()


def test_spike_mask_only_isolated_high_values():
    s = pd.Series([10.0, 100.0, 12.0, 90.0, 95.0, 20.0, 30.0, 50.0, 10.0])
    # 100: komşuları 10 ve 12 -> sıçrama. 90/95 ardışık yüksek -> gerçek olay, dokunulmaz.
    # 50: eşik (80) altında -> dokunulmaz.
    assert spike_mask(s).tolist() == [False, True, False, False, False, False, False, False, False]


def test_clean_station_rules_and_log():
    pm = [10.0, -1.0, 0.0, 12.0] + [7.0] * 6 + [15.0, 150.0, 14.0, 60.0]
    pm10 = [20.0] * 13 + [40.0]  # son saatte PM2.5 (60) > PM10 (40): sayılır, düzeltilmez
    df, log = clean_station(_sim(pm, pm10))
    assert log["≤0"] == 2
    assert log["takılı_sensör"] == 6
    assert log["tek_sıçrama"] == 1
    assert log["pm25>pm10"] == 1
    assert df["PM25"].iloc[-1] == 60.0
    assert log["kalan_ölçüm"] == len(pm) - 2 - 6 - 1
    # Hedef interpole edilmez
    assert df["PM25"].isna().sum() == 9


def test_clean_station_restores_hourly_grid():
    df = _sim([10.0, 11.0, 12.0]).drop(index=pd.Timestamp("2025-01-01 01:00"))
    out, _ = clean_station(df)
    assert len(out) == 3 and np.isnan(out["PM25"].iloc[1])
