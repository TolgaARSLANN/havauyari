"""Tahmin deposu: servis tahminleri buraya yazar ve buradan okur.

Okuma kuralı: bir kayıt yalnızca istenen tahmin saatinde (issued_at), aynı hedef saat için ve
aynı model sürümüyle üretilmişse kullanılır; aksi halde servis tahmini yeniden hesaplar ve
(istasyon, hedef saat) anahtarıyla üzerine yazar (upsert).
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import Engine, create_engine, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from havauyari.storage.models import AlertRow, ForecastRow, StationRow
from havauyari.storage.timeutil import decode_payload, encode_payload, to_local, to_utc

STATION_FIELDS = ("sim_id", "name", "city", "lat", "lon", "area_type", "source_type")


def normalize_url(url: str) -> str:
    """`postgresql://` ve `postgres://` adreslerini psycopg 3 sürücüsüne yönlendirir."""
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url.removeprefix(prefix)
    return url


def database_url() -> str | None:
    return os.environ.get("DATABASE_URL") or None


class ForecastRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    @classmethod
    def from_url(cls, url: str) -> ForecastRepository:
        # pool_pre_ping: veritabanı yeniden başlarsa kopmuş bağlantılar sessizce yenilenir
        return cls(create_engine(normalize_url(url), pool_pre_ping=True))

    def ping(self) -> None:
        with self.engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    # --- istasyonlar ---------------------------------------------------------------------
    def sync_stations(self, stations: Iterable[dict]) -> None:
        rows = [{"slug": s["slug"], **{k: s.get(k) for k in STATION_FIELDS}} for s in stations]
        if not rows:
            return
        stmt = insert(StationRow).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[StationRow.slug],
            set_={**{k: stmt.excluded[k] for k in STATION_FIELDS}, "updated_at": text("now()")})
        with Session(self.engine) as s, s.begin():
            s.execute(stmt)

    # --- tahminler -----------------------------------------------------------------------
    def get_forecast(self, station: str, issued_at: datetime, target_time: datetime,
                     model_version: str) -> dict | None:
        """Bu saatin, bu modelle verilmiş tahmini varsa yanıt sözlüğünü (yerel saatle) döner."""
        q = select(ForecastRow.payload).where(
            ForecastRow.station == station,
            ForecastRow.target_time == to_utc(target_time),
            ForecastRow.issued_at == to_utc(issued_at),
            ForecastRow.model_version == model_version)
        with Session(self.engine) as s:
            payload = s.execute(q).scalar_one_or_none()
        return None if payload is None else decode_payload(payload)

    def save_forecast(self, result: dict, model_version: str) -> None:
        """Tahmini ve uyarı durumunu tek işlemde yazar (aynı istasyon + hedef saat: upsert)."""
        key = {"station": result["station"], "target_time": to_utc(result["target_time"])}
        issued = to_utc(result["issued_at"])
        fc = insert(ForecastRow).values(
            **key, issued_at=issued, pm25=result["pm25"],
            low_80=result["interval_80"]["low"], high_80=result["interval_80"]["high"],
            model_version=model_version, payload=encode_payload(result))
        fc = fc.on_conflict_do_update(
            constraint="uq_forecasts_station_target",
            set_={c: fc.excluded[c] for c in ("issued_at", "pm25", "low_80", "high_80",
                                              "model_version", "payload")}
            | {"created_at": text("now()")})

        alert = result["alert"]
        values = {"issued_at": issued, "pm25": result["pm25"],
                  "decision_threshold": alert["decision_threshold"],
                  "is_alert": alert["is_alert"], "risk": alert["risk"]}
        with Session(self.engine) as s, s.begin():
            s.execute(fc)
            if alert["is_alert"] or alert["risk"]:
                al = insert(AlertRow).values(**key, **values)
                s.execute(al.on_conflict_do_update(
                    constraint="uq_alerts_station_target",
                    set_={c: al.excluded[c] for c in values} | {"updated_at": text("now()")}))
            else:                                    # uyarı kalktı: satır kalır, durum güncellenir
                s.execute(update(AlertRow)
                          .where(AlertRow.station == key["station"],
                                 AlertRow.target_time == key["target_time"])
                          .values(**values, updated_at=text("now()")))

    # --- uyarı geçmişi -------------------------------------------------------------------
    def alert_history(self, station: str | None = None) -> list[dict]:
        q = select(AlertRow).order_by(AlertRow.target_time, AlertRow.station)
        if station is not None:
            q = q.where(AlertRow.station == station)
        with Session(self.engine) as s:
            rows = s.execute(q).scalars().all()
        return [{"station": r.station, "issued_at": to_local(r.issued_at),
                 "target_time": to_local(r.target_time), "pm25": r.pm25,
                 "decision_threshold": r.decision_threshold, "is_alert": r.is_alert,
                 "risk": r.risk, "created_at": r.created_at, "updated_at": r.updated_at}
                for r in rows]


def repository_from_env() -> ForecastRepository | None:
    url = database_url()
    return None if url is None else ForecastRepository.from_url(url)
