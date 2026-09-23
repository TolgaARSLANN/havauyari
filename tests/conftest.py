"""Ortak test yardımcıları: sahte canlı veri sağlayıcısı ve sentetik küçük model.

API (test_api.py) ve pano (test_ui.py) testleri ağ ve gerçek model dosyası olmadan çalışır.
"""

import json
from datetime import datetime, timedelta

import lightgbm as lgb
import numpy as np
import pandas as pd
import pytest

from havauyari.config import POLLUTANTS, WEATHER_VARS
from havauyari.data.fetch_forecasts import FORECAST_VARS
from havauyari.features.build import build_station_features, feature_columns
from havauyari.serving.service import ForecastService, load_artifacts, prepare_frame

NOW = datetime(2026, 1, 15, 12)
STATIONS = [
    {"slug": "s1", "sim_id": "x1", "name": "Test - Bir", "city": "c1", "lat": 40.0,
     "lon": 29.0, "area_type": "Kentsel", "source_type": "Isınma"},
    {"slug": "s2", "sim_id": "x2", "name": "Test - İki", "city": "c2", "lat": 41.0,
     "lon": 28.9, "area_type": "Kentsel", "source_type": "Trafik"},
]


def synthetic_raw(station: dict, now: datetime, days: int = 12, seed: int = 0,
                  station_gap_hours: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range(now - timedelta(days=days), now + timedelta(days=2), freq="h")
    n = len(idx)
    df = pd.DataFrame(index=idx)
    for c in POLLUTANTS:
        df[c] = rng.uniform(5, 40, n)
    df["pm10"] = df["pm2_5"] * 1.4
    df["temperature_2m"] = rng.uniform(0, 15, n)
    df["relative_humidity_2m"] = rng.uniform(40, 90, n)
    df["wind_speed_10m"] = rng.uniform(0, 15, n)
    df["wind_direction_10m"] = rng.uniform(0, 360, n)
    df["precipitation"] = 0.0
    df["surface_pressure"] = rng.uniform(1000, 1020, n)
    for v in FORECAST_VARS:
        df[f"fc_{v}"] = df[v] if v in df else rng.uniform(0, 100, n)
    st = 10 + 0.8 * df["pm2_5"] - 0.5 * df["wind_speed_10m"] + rng.normal(0, 2, n)
    st[idx > now] = np.nan                                   # gelecek ölçüm yok
    if station_gap_hours:
        st[(idx > now - timedelta(hours=station_gap_hours)) & (idx <= now)] = np.nan
    df["station_pm25"] = st.clip(lower=1)
    df["station_pm10"] = df["station_pm25"] * 1.5
    df.insert(0, "city", station["city"])
    df.insert(0, "station", station["slug"])
    assert set(WEATHER_VARS) <= set(df.columns)
    return df


class FakeProvider:
    def __init__(self, gap_for=None, future_scale=1.0):
        self.calls = 0
        self.gap_for = gap_for or set()
        self.future_scale = future_scale

    def station_frame(self, station, now):
        self.calls += 1
        gap = 6 if station["slug"] in self.gap_for else 0
        df = synthetic_raw(station, now, station_gap_hours=gap,
                           seed=0 if station["slug"] == "s1" else 1)
        if self.future_scale != 1.0:                         # yalnızca gelecek gözlemleri boz
            obs = POLLUTANTS + WEATHER_VARS
            df.loc[df.index > now, obs] *= self.future_scale
        return df


@pytest.fixture(scope="session")
def models_dir(tmp_path_factory):
    """Sentetik geçmişle eğitilmiş küçük model + servis dosyaları."""
    d = tmp_path_factory.mktemp("models")
    parts = []
    for i, st in enumerate(STATIONS):
        raw = synthetic_raw(st, NOW - timedelta(days=5), days=60, seed=10 + i)
        f = build_station_features(prepare_frame(raw).assign(city=st["city"]), 24)
        f["station_code"], f["city_code"] = i, i
        parts.append(f)
    feats = pd.concat(parts).dropna(subset=["target_h24"])
    cols = feature_columns(feats, realistic=True)
    model = lgb.LGBMRegressor(n_estimators=40, num_leaves=15, verbose=-1)
    model.fit(feats[cols], feats["target_h24"])
    model.booster_.save_model(str(d / "test_model.txt"))

    (d / "model_card.json").write_text(json.dumps({
        "model": "test", "created": "2026-01-01", "trained_on": "sentetik",
        "model_file": "models/test_model.txt", "features": cols,
        "station_codes": {"s1": 0, "s2": 1}, "city_codes": {"c1": 0, "c2": 1},
        "backtest_12m": {"mae": 6.78, "cams_raw_mae": 12.95,
                         "alert_recall_station_thresholds": 0.8,
                         "alert_precision_station_thresholds": 0.55,
                         "interval_80_coverage": 0.83}}))
    (d / "prediction_interval.json").write_text(json.dumps({
        "bin_labels": ["<10", "10–20", "20–30", "30–45", "≥45"],
        "q_low": [-3, -5, -8, -12, -20], "q_high": [4, 7, 12, 18, 30]}))
    (d / "alert_threshold.json").write_text(json.dumps({
        "stations": {"s1": 0.0, "s2": 1000.0}, "default_threshold_ugm3": 28.5}))
    (d / "stations.json").write_text(json.dumps(STATIONS, ensure_ascii=False))
    return d


@pytest.fixture
def service(models_dir):
    return ForecastService(load_artifacts(models_dir), FakeProvider(), clock=lambda: NOW)
