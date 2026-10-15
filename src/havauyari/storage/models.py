"""Veritabanı şeması (SQLAlchemy 2.x). Değişiklikler Alembic migration'ıyla yapılır.

stations   istasyon kaydı (models/stations.json ile her açılışta eşitlenir)
forecasts  her (istasyon, hedef saat) için tek tahmin; yeniden hesaplanırsa üzerine yazılır
alerts     uyarı ya da uyarı riski görülen (istasyon, hedef saat) çiftleri; uyarı kalkınca
           satır silinmez, is_alert/risk false olur ve updated_at güncellenir (geçmiş korunur)
measurements  istasyonda gerçekleşen saatlik PM2.5 ölçümleri (canlı performans: tahmin - ölçüm)
runs       zamanlanmış toplama işinin (jobs.collect) her çalışmasının özeti
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

TZ = DateTime(timezone=True)                     # TIMESTAMPTZ: değerler UTC


class Base(DeclarativeBase):
    pass


class StationRow(Base):
    __tablename__ = "stations"

    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    sim_id: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(64))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    area_type: Mapped[str | None] = mapped_column(String(64))
    source_type: Mapped[str | None] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(TZ, server_default=func.now())


class ForecastRow(Base):
    __tablename__ = "forecasts"
    __table_args__ = (UniqueConstraint("station", "target_time",
                                       name="uq_forecasts_station_target"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    station: Mapped[str] = mapped_column(ForeignKey("stations.slug"), index=True)
    issued_at: Mapped[datetime] = mapped_column(TZ)
    target_time: Mapped[datetime] = mapped_column(TZ)
    pm25: Mapped[float] = mapped_column(Float)
    low_80: Mapped[float] = mapped_column(Float)
    high_80: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(128))
    payload: Mapped[dict] = mapped_column(JSONB)   # API yanıtının tamamı (zamanlar UTC)
    created_at: Mapped[datetime] = mapped_column(TZ, server_default=func.now())


class AlertRow(Base):
    __tablename__ = "alerts"
    __table_args__ = (UniqueConstraint("station", "target_time",
                                       name="uq_alerts_station_target"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    station: Mapped[str] = mapped_column(ForeignKey("stations.slug"), index=True)
    issued_at: Mapped[datetime] = mapped_column(TZ)
    target_time: Mapped[datetime] = mapped_column(TZ)
    pm25: Mapped[float] = mapped_column(Float)
    decision_threshold: Mapped[float] = mapped_column(Float)
    is_alert: Mapped[bool] = mapped_column(Boolean)
    risk: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(TZ, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TZ, server_default=func.now())


class MeasurementRow(Base):
    __tablename__ = "measurements"

    station: Mapped[str] = mapped_column(ForeignKey("stations.slug"), primary_key=True)
    time: Mapped[datetime] = mapped_column(TZ, primary_key=True)
    pm25: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(TZ, server_default=func.now())


class RunRow(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(TZ)
    finished_at: Mapped[datetime] = mapped_column(TZ)
    issued_at: Mapped[datetime] = mapped_column(TZ)          # tahminlerin verildiği saat
    ok: Mapped[int] = mapped_column(Integer)
    failed: Mapped[int] = mapped_column(Integer)
    measurements: Mapped[int] = mapped_column(Integer)
    errors: Mapped[dict] = mapped_column(JSONB)              # {istasyon: hata metni}
