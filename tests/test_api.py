"""API uçtan uca testleri: ağ ve gerçek model dosyası olmadan (sahte sağlayıcı + küçük model)."""

from datetime import timedelta

import pytest
from conftest import NOW, FakeProvider
from fastapi.testclient import TestClient

from havauyari.serving.app import create_app
from havauyari.serving.service import ForecastService, load_artifacts


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


def test_trajectory_and_history(client):
    f = client.get("/forecast/s1").json()
    traj = f["trajectory"]
    assert len(traj) == 96                                   # 72 + 24 saat, her saat bir tahmin
    last = traj[-1]
    assert last["issued_at"] == f["issued_at"] and last["pm25"] == f["pm25"]
    future = [p for p in traj if p["target_time"] > f["issued_at"]]
    assert len(future) == 24 and all(p["actual"] is None for p in future)
    past = [p for p in traj if p["target_time"] <= f["issued_at"]]
    assert all(p["actual"] is not None for p in past)       # geçmiş hedefler ölçülmüş
    assert all(p["low"] <= p["pm25"] <= p["high"] for p in traj)
    assert len(f["history"]) == 72 and f["history"][-1]["time"] == f["issued_at"]


def test_second_station_not_alert(client):
    assert client.get("/forecast/s2").json()["alert"]["is_alert"] is False   # eşik 1000


def test_unknown_station_404(client):
    r = client.get("/forecast/yok")
    assert r.status_code == 404 and "Geçerli" in r.json()["detail"]


def test_stale_station_data_503(models_dir):
    svc = ForecastService(load_artifacts(models_dir), FakeProvider(gap_for={"s1"}),
                          clock=lambda: NOW)
    r = TestClient(create_app(svc)).get("/forecast/s1")
    assert r.status_code == 503 and "ölçümü yapılmamış" in r.json()["detail"]


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
