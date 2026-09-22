import numpy as np
import pandas as pd
import pytest

from havauyari.config import POLLUTANTS, WEATHER_VARS
from havauyari.features.build import (
    build_all_cities,
    build_features,
    feature_columns,
    is_holiday,
)


def _series(n=400, city="x", start="2024-01-01"):
    idx = pd.date_range(start, periods=n, freq="h")
    return pd.DataFrame({"city": city, "pm2_5": np.arange(n, dtype=float)}, index=idx)


def _full_frame(n=600, seed=0, start="2025-03-20"):
    """Tüm ham sütunları içeren gerçekçi rastgele tablo."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, periods=n, freq="h")
    data = {c: rng.uniform(1, 80, n) for c in POLLUTANTS}
    data["pm10"] = data["pm2_5"] * rng.uniform(1.1, 1.6, n)
    data.update({
        "temperature_2m": rng.uniform(-5, 35, n),
        "relative_humidity_2m": rng.uniform(10, 100, n),
        "wind_speed_10m": rng.uniform(0, 30, n),
        "wind_direction_10m": rng.uniform(0, 360, n),
        "surface_pressure": rng.uniform(980, 1030, n),
        "precipitation": rng.choice([0.0, 0.0, 0.0, 0.5, 2.0], n),
    })
    assert set(WEATHER_VARS) <= set(data)
    df = pd.DataFrame(data, index=idx)
    df.insert(0, "city", "test")
    return df


# --- Genel sızıntı testi (Faz 2.4) -------------------------------------------------------------
@pytest.mark.parametrize("horizon", [1, 6, 24, 48, 72])
def test_no_feature_uses_future_values(horizon):
    """t0 sonrasındaki TÜM ölçümler değiştirildiğinde t0 ve öncesindeki hiçbir özellik değişmemeli.

    Yeni eklenen her özellik bu testten otomatik olarak geçer; tek tek test yazmaya gerek kalmaz.
    """
    df = _full_frame()
    t0 = df.index[400]
    perturbed = df.copy()
    num = perturbed.columns.drop("city")
    after = perturbed.index > t0
    perturbed.loc[after, num] = perturbed.loc[after, num] * 3 + 7

    a = build_features(df, horizon)
    b = build_features(perturbed, horizon)
    cols = feature_columns(a)
    pd.testing.assert_frame_equal(a.loc[:t0, cols], b.loc[:t0, cols])
    # Kontrol: hedef ise gerçekten gelecekten gelmeli ve değişmeli
    assert not a.loc[:t0, f"target_h{horizon}"].equals(b.loc[:t0, f"target_h{horizon}"])


def _with_forecasts(df, seed=1):
    rng = np.random.default_rng(seed)
    n = len(df)
    out = df.copy()
    out["fc_temperature_2m"] = rng.uniform(-5, 35, n)
    out["fc_relative_humidity_2m"] = rng.uniform(10, 100, n)
    out["fc_wind_speed_10m"] = rng.uniform(0, 30, n)
    out["fc_wind_direction_10m"] = rng.uniform(0, 360, n)
    out["fc_precipitation"] = rng.choice([0.0, 0.0, 1.0], n)
    out["fc_surface_pressure"] = rng.uniform(980, 1030, n)
    out["fc_cloud_cover"] = rng.uniform(0, 100, n)
    return out


@pytest.mark.parametrize("horizon", [1, 6, 24])
def test_forecast_features_respect_publication_window(horizon):
    """Faz 3.8 sızıntı kuralı: t anında yalnızca (t, t+h] geçerlilikli day1 tahminleri kullanılır.

    1) t0 sonrası gözlemler ve t0+h sonrası tahminler bozulursa t0 özellikleri DEĞİŞMEMELİ.
    2) (t0, t0+h] içindeki tahminler bozulursa t0 özellikleri DEĞİŞMELİ (gerçekten kullanılıyor).
    """
    df = _with_forecasts(_full_frame())
    t0 = df.index[400]
    fc_cols = [c for c in df.columns if c.startswith("fc_")]
    obs_cols = [c for c in df.columns if c not in fc_cols and c != "city"]

    outside = df.copy()
    outside.loc[outside.index > t0, obs_cols] *= 3
    outside.loc[outside.index > t0 + pd.Timedelta(hours=horizon), fc_cols] *= 3
    a, b = build_features(df, horizon), build_features(outside, horizon)
    cols = feature_columns(a)
    pd.testing.assert_frame_equal(a.loc[:t0, cols], b.loc[:t0, cols])

    inside = df.copy()
    win = (inside.index > t0) & (inside.index <= t0 + pd.Timedelta(hours=horizon))
    inside.loc[win, fc_cols] = inside.loc[win, fc_cols] * 2 + 1
    c = build_features(inside, horizon)
    fc_feats = [x for x in cols if x.startswith("fc_")]
    assert fc_feats and not a.loc[t0, fc_feats].equals(c.loc[t0, fc_feats])


def test_forecast_window_semantics():
    n = 60
    idx = pd.date_range("2025-01-01", periods=n, freq="h")
    df = pd.DataFrame({"city": "x", "pm2_5": 10.0, "temperature_2m": 5.0,
                       "fc_precipitation": np.arange(n, dtype=float),
                       "fc_temperature_2m": np.arange(n, dtype=float),
                       "fc_wind_speed_10m": [2.0] * 30 + [10.0] * 30}, index=idx)
    out = build_features(df, 6)
    t = 20
    assert out["fc_win_precip_sum"].iloc[t] == sum(range(t + 1, t + 7))   # (t, t+6]
    assert out["fc_tgt_temperature"].iloc[t] == t + 6
    assert out["fc_tgt_temp_change"].iloc[t] == t + 6 - 5.0
    assert out["fc_win_temp_range"].iloc[t] == 5.0
    assert out["fc_win_calm_hours"].iloc[t] == 6          # 21..26 < 4 km/sa
    assert out["fc_win_calm_hours"].iloc[26] == 3         # 27,28,29 durgun; 30,31,32 değil
    assert not any(c in out for c in ["fc_precipitation", "fc_temperature_2m"])  # ham sütun yok


def test_forecast_horizon_limit():
    df = _with_forecasts(_full_frame(100))
    with pytest.raises(ValueError, match="en fazla 24"):
        build_features(df, 48)
    # Tahmin sütunu yoksa uzun ufuk sorun değil
    assert "fc_tgt_temperature" not in build_features(_full_frame(100), 48)


def test_all_expected_feature_groups_present():
    out = build_features(_full_frame(), 24)
    cols = set(feature_columns(out))
    expected = {
        "pm2_5_lag24", "pm2_5_rollmax24", "pm2_5_diff24",                      # 2.1
        "is_holiday", "tgt_is_holiday", "tgt_hour_sin", "tgt_dayofweek",       # 2.2
        "calm_hours24", "precip_sum24", "heating_degree", "temp_range24",      # 2.3
        "pressure_diff24", "wind_u_rollmean24", "pm10_lag24",
        "nitrogen_dioxide_rollmean24", "pm_ratio",
        "pm2_5_tgt_day_ago", "pm2_5_tgt_week_ago",
    }
    assert expected <= cols
    assert not any(c.startswith("target_") for c in cols)


# --- PM2.5 geçmişi (Faz 2.1) -------------------------------------------------------------------
def test_target_lags_and_rolling():
    out = build_features(_series(), 24)
    row = out.loc[out.index[200]]
    assert row["pm2_5_lag1"] == 199
    assert row["pm2_5_rollmean6"] == np.mean(range(194, 200))
    assert row["pm2_5_rollmax24"] == 199
    assert row["pm2_5_diff24"] == 24
    assert row["target_h24"] == 224


@pytest.mark.parametrize("horizon, expected_lag", [(1, 23), (6, 18), (24, 0), (30, 18), (48, 0)])
def test_target_aligned_day_ago(horizon, expected_lag):
    """pm2_5_tgt_day_ago: hedef saatle aynı saatteki en son gözlem (t+h-24k ≤ t)."""
    out = build_features(_series(), horizon)
    t = 300
    assert out["pm2_5_tgt_day_ago"].iloc[t] == t - expected_lag
    target_hour = out.index[t + horizon].hour
    assert out.index[t - expected_lag].hour == target_hour


def test_target_aligned_week_ago():
    out = build_features(_series(), 24)
    assert out["pm2_5_tgt_week_ago"].iloc[300] == 300 - 144


def test_lags_do_not_cross_cities():
    df = pd.concat([_series(200, "a"), _series(200, "b")])
    out = build_all_cities(df)
    first_b = out[out["city"] == "b"].iloc[0]
    assert np.isnan(first_b["pm2_5_lag1"])


# --- Takvim ve tatiller (Faz 2.2) --------------------------------------------------------------
def test_turkish_holidays():
    idx = pd.DatetimeIndex(["2025-03-28 10:00", "2025-03-31 10:00", "2025-06-07 03:00",
                            "2025-10-29 23:00", "2025-10-30 00:00"])
    assert is_holiday(idx).tolist() == [0, 1, 1, 1, 0]


def test_target_calendar_uses_target_time():
    df = _series(200, start="2025-03-28 00:00")  # 30 Mart Pazar = Ramazan Bayramı 1. gün
    out = build_features(df, 24)
    t = pd.Timestamp("2025-03-29 21:00")         # hedef: 30 Mart 21:00
    row = out.loc[t]
    assert row["is_holiday"] == 0
    assert row["tgt_is_holiday"] == 1
    assert row["tgt_dayofweek"] == 6
    assert row["tgt_is_weekend"] == 1
    assert np.isclose(row["tgt_hour_sin"], np.sin(2 * np.pi * 21 / 24))

    out6 = build_features(df, 6)
    assert np.isclose(out6.loc[t, "tgt_hour_sin"], np.sin(2 * np.pi * 3 / 24))  # 21:00 + 6s


# --- Meteoroloji ve kirleticiler (Faz 2.3) -----------------------------------------------------
def test_meteorology_features():
    n = 48
    idx = pd.date_range("2025-01-01", periods=n, freq="h")
    df = pd.DataFrame({
        "city": "x",
        "pm2_5": 10.0,
        "wind_speed_10m": [2.0] * 24 + [10.0] * 24,
        "wind_direction_10m": 90.0,   # doğudan
        "precipitation": [0.0] * 46 + [1.0, 2.0],
        "temperature_2m": [0.0] * 24 + [20.0] * 24,
        "surface_pressure": [1000.0] * 24 + [1010.0] * 24,
    }, index=idx)
    out = build_features(df, 24)
    last = out.iloc[-1]
    assert out["calm_hours24"].iloc[23] == 24
    assert last["calm_hours24"] == 0
    assert last["precip_sum3"] == 3.0 and last["precip_sum24"] == 3.0
    assert out["heating_degree"].iloc[0] == 15.0 and last["heating_degree"] == 0.0
    assert last["temp_diff24"] == 20.0
    assert last["pressure_diff24"] == 10.0
    assert np.isclose(last["wind_u"], 10.0) and np.isclose(last["wind_v"], 0.0, atol=1e-9)
    assert out["temp_range24"].iloc[30] == 20.0


def test_pollutant_features():
    df = _full_frame(100)
    out = build_features(df, 24)
    t = 50
    assert out["pm10_lag24"].iloc[t] == df["pm10"].iloc[t - 24]
    assert np.isclose(out["ozone_rollmean24"].iloc[t], df["ozone"].iloc[t - 23 : t + 1].mean())
    assert np.isclose(out["pm_ratio"].iloc[t], df["pm2_5"].iloc[t] / df["pm10"].iloc[t])
