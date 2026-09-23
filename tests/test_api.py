"""API uçtan uca testleri: ağ ve gerçek model dosyası olmadan (sahte sağlayıcı + küçük model)."""

import json
from datetime import datetime, timedelta

import lightgbm as lgb
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from havauyari.config import POLLUTANTS, WEATHER_VARS
from havauyari.data.fetch_forecasts import FORECAST_VARS
from havauyari.features.build import build_station_features, feature_columns
from havauyari.serving.app import create_app
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


@pytest.fixture(scope="module")
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
        "station_codes": {"s1": 0, "s2": 1}, "city_codes": {"c1": 0, "c2": 1}}))
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


@pytest.fixture
def client(service):
    return TestClient(create_app(service))


def test_health_and_stations(client):
    h = client.get("/health").json()
    assert h["status"] == "ok" and h["model_loaded"] and h["stations"] == 2
    st = client.get("/stations").json()
    assert {s["slug"] for s in st} == {"s1", "s2"}
    assert {s["slug"]: s["decision_threshold"] for s in st} == {"s1": 0.0, "s2": 1000.0}


def test_forecast_payload(client, service):
    r = client.get("/forecast/s1")
    assert r.status_code == 200
    f = r.json()
    assert f["station"] == "s1" and f["city"] == "c1"
    assert f["issued_at"] == "2026-01-15T12:00:00"
    assert f["target_time"] == "2026-01-16T12:00:00"
    assert f["interval_80"]["low"] <= f["pm25"] <= f["interval_80"]["high"]
    assert f["alert"]["is_alert"] is True                      # s1 eşiği 0
    assert f["alert"]["official_threshold"] == 35.5
    assert len(f["explanation"]["top_features"]) == 5
    e = f["explanation"]
    total = e["base_value"] + sum(c["contribution"] for c in e["top_features"]) \
        + e["other_features"]
    assert total == pytest.approx(f["pm25"], abs=0.1)          # katkılar tahmini açıklar
    assert f["latest_measurement"]["time"] == "2026-01-15T12:00:00"


def test_second_station_not_alert(client):
    assert client.get("/forecast/s2").json()["alert"]["is_alert"] is False   # eşik 1000


def test_unknown_station_404(client):
    r = client.get("/forecast/yok")
    assert r.status_code == 404 and "Geçerli" in r.json()["detail"]


def test_stale_station_data_503(models_dir):
    svc = ForecastService(load_artifacts(models_dir), FakeProvider(gap_for={"s1"}),
                          clock=lambda: NOW)
    r = TestClient(create_app(svc)).get("/forecast/s1")
    assert r.status_code == 503 and "ölçümü yok" in r.json()["detail"]


def test_same_hour_is_cached_new_hour_refetches(models_dir):
    provider = FakeProvider()
    clock = {"now": NOW}
    svc = ForecastService(load_artifacts(models_dir), provider, clock=lambda: clock["now"])
    svc.forecast("s1")
    svc.forecast("s1")
    assert provider.calls == 1
    clock["now"] = NOW + timedelta(hours=1)
    svc.forecast("s1")
    assert provider.calls == 2


def test_future_observations_do_not_change_forecast(models_dir):
    """Gelecekteki CAMS/meteoroloji değerleri (tahmin olarak gelse bile) gerçekçi modele girmez."""
    a = ForecastService(load_artifacts(models_dir), FakeProvider(), clock=lambda: NOW)
    b = ForecastService(load_artifacts(models_dir), FakeProvider(future_scale=5.0),
                        clock=lambda: NOW)
    assert a.forecast("s1")["pm25"] == b.forecast("s1")["pm25"]


def test_alerts_endpoint_filters(client):
    all_ = client.get("/alerts").json()
    assert {x["station"] for x in all_} == {"s1", "s2"}
    only = client.get("/alerts", params={"only_alerts": True}).json()
    assert "s1" in {x["station"] for x in only}


def test_health_without_model(monkeypatch):
    import havauyari.serving.service as svc

    def missing(*_a, **_k):
        raise FileNotFoundError("Model dosyası yok")

    monkeypatch.setattr(svc, "load_artifacts", missing)
    c = TestClient(create_app())
    h = c.get("/health").json()
    assert h["model_loaded"] is False and "Model" in h["detail"]
    assert c.get("/stations").status_code == 503
