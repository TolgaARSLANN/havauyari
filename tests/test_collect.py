"""Toplama işi (jobs.collect) testleri.

Veritabanı gerektirenler `db` işaretlidir ve TEST_DATABASE_URL yoksa atlanır; giriş noktasının
(main) hata yolları veritabanı olmadan da sınanır.
"""

from datetime import UTC, datetime

import pytest
from conftest import NOW, TEST_DATABASE_URL, FakeProvider

from havauyari.jobs import collect as job
from havauyari.serving.service import ForecastService, load_artifacts

NOW_UTC = datetime(2026, 1, 15, 9, tzinfo=UTC)          # NOW = 12.00 Türkiye saati
db = pytest.mark.db
needs_db = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL tanımlı değil")


class FailingProvider(FakeProvider):
    """Belirli istasyonlarda ağ hatası verir (ör. SİM zaman aşımı)."""

    def __init__(self, fail_for, **kw):
        super().__init__(**kw)
        self.fail_for = set(fail_for)

    def station_frame(self, station, now):
        if station["slug"] in self.fail_for:
            raise ConnectionError("SİM yanıt vermedi")
        return super().station_frame(station, now)


def make_service(models_dir, repo, provider=None):
    return ForecastService(load_artifacts(models_dir), provider or FakeProvider(),
                           clock=lambda: NOW, repository=repo)


def rows(repo, sql):
    from sqlalchemy import text

    with repo.engine.connect() as c:
        return c.execute(text(sql)).mappings().all()


# --- veritabanıyla -----------------------------------------------------------------------------
@db
@needs_db
def test_collect_saves_forecasts_measurements_and_run(models_dir, clean_db):
    svc = make_service(models_dir, clean_db)
    clean_db.sync_stations(svc.a.stations.values())
    result = job.collect(svc)

    assert result.ok == ["s1", "s2"] and result.errors == {} and result.exit_code == 0
    assert len(rows(clean_db, "SELECT id FROM forecasts")) == 2
    measured = rows(clean_db, "SELECT station, time, pm25 FROM measurements ORDER BY time")
    assert len(measured) == result.measurements == 2 * 72        # son 72 saat, iki istasyon
    assert measured[-1]["time"] == NOW_UTC                         # UTC olarak saklanır
    (run,) = rows(clean_db, "SELECT * FROM runs")
    assert (run["ok"], run["failed"], run["measurements"]) == (2, 0, 144)
    assert run["issued_at"] == NOW_UTC and run["errors"] == {}
    assert run["started_at"] <= run["finished_at"]


@db
@needs_db
def test_rerun_in_same_hour_is_idempotent(models_dir, clean_db):
    job.collect(make_service(models_dir, clean_db))
    provider = FakeProvider()
    job.collect(make_service(models_dir, clean_db, provider))
    assert provider.calls == 0                                     # tahminler DB'den okundu
    assert len(rows(clean_db, "SELECT id FROM forecasts")) == 2
    assert len(rows(clean_db, "SELECT time FROM measurements")) == 144   # üzerine yazıldı
    assert len(rows(clean_db, "SELECT id FROM runs")) == 2               # her çalışma kayıtlı


@db
@needs_db
def test_station_without_data_does_not_stop_others(models_dir, clean_db):
    result = job.collect(make_service(models_dir, clean_db, FakeProvider(gap_for={"s1"})))
    assert result.ok == ["s2"] and "ölçümü yapılmamış" in result.errors["s1"]
    assert result.exit_code == 0
    (run,) = rows(clean_db, "SELECT ok, failed, errors FROM runs")
    assert (run["ok"], run["failed"]) == (1, 1) and "s1" in run["errors"]


@db
@needs_db
def test_network_error_is_recorded_and_skipped(models_dir, clean_db):
    result = job.collect(make_service(models_dir, clean_db, FailingProvider({"s2"})))
    assert result.ok == ["s1"]
    assert result.errors["s2"] == "ConnectionError: SİM yanıt vermedi"


@db
@needs_db
def test_all_stations_failing_exits_1(models_dir, clean_db):
    result = job.collect(make_service(models_dir, clean_db, FailingProvider({"s1", "s2"})))
    assert result.ok == [] and result.exit_code == 1
    assert rows(clean_db, "SELECT failed FROM runs")[0]["failed"] == 2


# --- veritabanı olmadan ------------------------------------------------------------------------
def test_collect_requires_repository(models_dir):
    with pytest.raises(ValueError):
        job.collect(make_service(models_dir, None))


def test_main_without_database_url_exits_2(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert job.main() == 2


def test_main_with_unreachable_database_exits_1(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://x:y@127.0.0.1:1/yok?connect_timeout=2")
    assert job.main() == 1
