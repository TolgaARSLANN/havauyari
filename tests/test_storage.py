"""PostgreSQL entegrasyon testleri (pytest -m db).

TEST_DATABASE_URL tanımlı değilse atlanır. Bu veritabanının tabloları her oturumda silinip
migration'larla yeniden kurulur: gerçek veri içeren bir veritabanı vermeyin.
CI'da GitHub Actions'ın postgres servis konteyneriyle, yerelde `make test-db` ile çalışır.
"""

import copy
from datetime import UTC, datetime, timedelta

import pytest
from conftest import NOW, TEST_DATABASE_URL, FakeProvider
from fastapi.testclient import TestClient

from havauyari.serving.app import create_app
from havauyari.serving.service import ForecastService, load_artifacts

pytestmark = [pytest.mark.db, pytest.mark.skipif(not TEST_DATABASE_URL,
                                                 reason="TEST_DATABASE_URL tanımlı değil")]

if TEST_DATABASE_URL:
    from sqlalchemy import text

NOW_UTC = datetime(2026, 1, 15, 9, tzinfo=UTC)          # NOW = 12.00 Türkiye saati (UTC+3)


@pytest.fixture
def repo(clean_db):
    return clean_db                                      # boş tablolarla (conftest)


def make_service(models_dir, repo, provider=None, clock=lambda: NOW):
    return ForecastService(load_artifacts(models_dir), provider or FakeProvider(), clock=clock,
                           repository=repo)


def rows(repo, sql: str) -> list:
    with repo.engine.connect() as c:
        return c.execute(text(sql)).mappings().all()


# --- şema ------------------------------------------------------------------------------------
def test_migrations_match_models(repo):
    """Alembic migration'ı ile SQLAlchemy modelleri arasında fark yok."""
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext

    from havauyari.storage.models import Base

    with repo.engine.connect() as c:
        diff = compare_metadata(MigrationContext.configure(c), Base.metadata)
    assert diff == []


def test_time_columns_are_timestamptz(repo):
    cols = rows(repo, "SELECT table_name, column_name, data_type FROM information_schema.columns "
                      "WHERE table_schema = 'public' AND data_type LIKE 'timestamp%'")
    assert cols and all(c["data_type"] == "timestamp with time zone" for c in cols)


# --- tahmin yazma / okuma -------------------------------------------------------------------
def test_forecast_written_in_utc_and_read_back_in_local_time(models_dir, repo):
    computed = make_service(models_dir, repo).forecast("s1")
    (row,) = rows(repo, "SELECT * FROM forecasts")
    assert row["issued_at"] == NOW_UTC
    assert row["target_time"] == NOW_UTC + timedelta(hours=24)
    assert row["pm25"] == computed["pm25"]
    assert (row["low_80"], row["high_80"]) == (computed["interval_80"]["low"],
                                               computed["interval_80"]["high"])
    assert row["model_version"] == "test@2026-01-01"
    assert row["payload"]["issued_at"] == "2026-01-15T09:00:00+00:00"   # JSON içinde de UTC

    provider = FakeProvider()
    from_db = make_service(models_dir, repo, provider).forecast("s1")   # yeni süreç gibi
    assert provider.calls == 0                                         # yeniden hesaplanmadı
    assert from_db == computed                                         # yerel saat, aynı yanıt


def test_api_response_identical_from_db(models_dir, repo):
    first = TestClient(create_app(make_service(models_dir, repo))).get("/forecast/s1")
    provider = FakeProvider()
    second = TestClient(create_app(make_service(models_dir, repo, provider))).get("/forecast/s1")
    assert provider.calls == 0
    assert second.status_code == 200 and second.json() == first.json()
    assert second.json()["issued_at"] == "2026-01-15T12:00:00"         # şema değişmedi


def test_upsert_keeps_one_row_per_station_and_target(models_dir, repo):
    svc = make_service(models_dir, repo)
    result = svc.forecast("s1")
    changed = copy.deepcopy(result) | {"pm25": result["pm25"] + 5}
    repo.save_forecast(changed, svc.model_version)
    (row,) = rows(repo, "SELECT pm25 FROM forecasts")
    assert row["pm25"] == result["pm25"] + 5


def test_other_issue_hour_is_recomputed(models_dir, repo):
    """Kayıt aynı hedef saate ait ama bu saatte verilmemiş: kullanılmaz, yeniden hesaplanır."""
    make_service(models_dir, repo).forecast("s1")
    with repo.engine.begin() as c:
        c.execute(text("UPDATE forecasts SET issued_at = issued_at - interval '1 hour', "
                       "payload = jsonb_set(payload, '{pm25}', '-1')"))
    provider = FakeProvider()
    result = make_service(models_dir, repo, provider).forecast("s1")
    assert provider.calls == 1 and result["pm25"] != -1
    (row,) = rows(repo, "SELECT issued_at FROM forecasts")
    assert row["issued_at"] == NOW_UTC                                  # üzerine yazıldı


def test_other_model_version_is_recomputed(models_dir, repo):
    make_service(models_dir, repo).forecast("s1")
    with repo.engine.begin() as c:
        c.execute(text("UPDATE forecasts SET model_version = 'eski@2025-01-01'"))
    provider = FakeProvider()
    make_service(models_dir, repo, provider).forecast("s1")
    assert provider.calls == 1
    assert rows(repo, "SELECT model_version FROM forecasts")[0]["model_version"] == \
        "test@2026-01-01"


def test_new_hour_adds_new_row(models_dir, repo):
    clock = {"now": NOW}
    svc = make_service(models_dir, repo, clock=lambda: clock["now"])
    svc.forecast("s1")
    clock["now"] = NOW + timedelta(hours=1)
    svc.forecast("s1")
    assert len(rows(repo, "SELECT id FROM forecasts")) == 2


def test_stations_synced(models_dir, repo):
    make_service(models_dir, repo).forecast("s1")
    assert {r["slug"] for r in rows(repo, "SELECT slug FROM stations")} == {"s1", "s2"}


# --- uyarılar --------------------------------------------------------------------------------
def with_alert(result: dict, is_alert: bool, risk: bool) -> dict:
    out = copy.deepcopy(result)
    out["alert"] |= {"is_alert": is_alert, "risk": risk}
    return out


def test_alert_opens_then_closes_row_is_kept(models_dir, repo):
    svc = make_service(models_dir, repo)
    result = svc.forecast("s1")                                        # s1 eşiği 0: uyarı var
    (opened,) = repo.alert_history("s1")
    assert opened["is_alert"] is True
    assert opened["target_time"] == result["target_time"]              # yerel saate döndü

    repo.save_forecast(with_alert(result, False, False), svc.model_version)
    (closed,) = repo.alert_history("s1")                               # satır silinmedi
    assert closed["is_alert"] is False and closed["risk"] is False
    assert closed["created_at"] == opened["created_at"]
    assert closed["updated_at"] > opened["updated_at"]


def test_no_alert_row_without_alert_or_risk(models_dir, repo):
    svc = make_service(models_dir, repo)
    result = svc.forecast("s1")
    with repo.engine.begin() as c:
        c.execute(text("TRUNCATE alerts"))
    repo.save_forecast(with_alert(result, False, False), svc.model_version)
    assert repo.alert_history() == []


def test_risk_only_creates_alert_row(models_dir, repo):
    svc = make_service(models_dir, repo)
    result = svc.forecast("s1")
    repo.save_forecast(with_alert(result, False, True), svc.model_version)
    (row,) = repo.alert_history("s1")
    assert row["is_alert"] is False and row["risk"] is True


def test_alerts_endpoint_persists_all_stations(models_dir, repo):
    client = TestClient(create_app(make_service(models_dir, repo)))
    first = client.get("/alerts").json()
    assert {r["station"] for r in rows(repo, "SELECT station FROM forecasts")} == {"s1", "s2"}
    assert "s1" in {a["station"] for a in repo.alert_history() if a["is_alert"]}

    provider = FakeProvider()
    again = TestClient(create_app(make_service(models_dir, repo, provider))).get("/alerts")
    assert provider.calls == 0 and again.json() == first              # DB'den okundu


# --- sağlık ----------------------------------------------------------------------------------
def test_health_reports_database_ok(models_dir, repo):
    h = TestClient(create_app(make_service(models_dir, repo))).get("/health").json()
    assert h["database"] == "ok" and h["status"] == "ok"
