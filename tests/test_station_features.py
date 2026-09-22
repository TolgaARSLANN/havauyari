"""İstasyon hedefli özellik akışının testleri (Faz 3.9)."""

import numpy as np
import pandas as pd
import pytest

from havauyari.features.build import (
    build_all_stations,
    build_station_features,
    feature_columns,
)

H = 24


def _station_frame(n=300, station="s1", seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2025-06-01", periods=n, freq="h")
    df = pd.DataFrame({
        "station": station,
        "city": "c1",
        "pm2_5": rng.uniform(5, 60, n),          # CAMS
        "pm10": rng.uniform(10, 90, n),
        "temperature_2m": rng.uniform(0, 30, n),
        "wind_speed_10m": rng.uniform(0, 20, n),
        "wind_direction_10m": rng.uniform(0, 360, n),
        "precipitation": 0.0,
        "relative_humidity_2m": rng.uniform(20, 90, n),
        "surface_pressure": rng.uniform(990, 1020, n),
        "station_pm25": rng.uniform(5, 70, n),
        "station_pm10": rng.uniform(10, 90, n),
    }, index=idx)
    return df


def test_target_is_raw_measurement_and_gaps_are_not_filled():
    df = _station_frame()
    df.loc[df.index[100:104], "station_pm25"] = np.nan   # 4 saatlik boşluk
    out = build_station_features(df, H)
    target = out[f"target_h{H}"]
    # Hedef ham ölçüm: boşluk saatleri hedef olarak da boş kalır
    assert target.iloc[100 - H : 104 - H].isna().all()
    assert np.isclose(target.iloc[50], df["station_pm25"].iloc[50 + H])


def test_feature_gaps_filled_from_past_only():
    df = _station_frame()
    before = df["station_pm25"].iloc[99]
    df.loc[df.index[100:104], "station_pm25"] = np.nan
    out = build_station_features(df, H)
    # İlk 3 saat geçmiş değerle taşınır, 4. saat boş kalır (interpolasyon yok)
    assert (out["station_pm25"].iloc[100:103] == before).all()
    assert np.isnan(out["station_pm25"].iloc[103])


def test_station_features_do_not_use_future_station_values():
    df = _station_frame()
    t0 = df.index[200]
    perturbed = df.copy()
    after = perturbed.index > t0
    perturbed.loc[after, "station_pm25"] *= 5
    a, b = build_station_features(df, H), build_station_features(perturbed, H)
    cols = [c for c in feature_columns(a) if not c.startswith("cams_")]
    pd.testing.assert_frame_equal(a.loc[:t0, cols], b.loc[:t0, cols])


def test_cams_forecast_features_are_target_aligned():
    df = _station_frame()
    df["pm2_5"] = np.arange(len(df), dtype=float)
    out = build_station_features(df, H)
    t = 100
    assert out["cams_tgt"].iloc[t] == t + H
    assert out["cams_tgt_lag3"].iloc[t] == t + H - 3
    assert out["cams_win_mean"].iloc[t] == np.mean(range(t + 1, t + H + 1))
    assert out["cams_win_max"].iloc[t] == t + H


def test_realistic_feature_set_excludes_future_cams():
    out = build_station_features(_station_frame(), H)
    realistic = feature_columns(out, realistic=True)
    optimistic = feature_columns(out)
    assert not any(c.startswith("cams_") for c in realistic)
    assert any(c.startswith("cams_") for c in optimistic)
    assert set(realistic) < set(optimistic)
    for cols in (realistic, optimistic):
        assert "station" not in cols and "city" not in cols


@pytest.mark.parametrize("col", ["station_pm25", "pm2_5"])
def test_realistic_features_use_only_past_of_that_column(col):
    """Gerçekçi özellik setinde hiçbir sütunun geleceği kullanılmamalı."""
    df = _station_frame()
    t0 = df.index[200]
    perturbed = df.copy()
    perturbed.loc[perturbed.index > t0, col] *= 4
    a, b = build_station_features(df, H), build_station_features(perturbed, H)
    cols = feature_columns(a, realistic=True)
    pd.testing.assert_frame_equal(a.loc[:t0, cols], b.loc[:t0, cols])


def test_build_all_stations_keeps_stations_separate():
    df = pd.concat([_station_frame(200, "s1", 0), _station_frame(200, "s2", 1)])
    out = build_all_stations(df, H)
    first_s2 = out[out["station"] == "s2"].iloc[0]
    assert np.isnan(first_s2["station_pm25_lag1"])
    assert out["station"].nunique() == 2
