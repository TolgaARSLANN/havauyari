"""API yanıt şemaları (Pydantic). FastAPI bunlardan /docs sayfasını otomatik üretir."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Interval(BaseModel):
    low: float = Field(description="%80 aralığın alt sınırı (µg/m³)")
    high: float = Field(description="%80 aralığın üst sınırı (µg/m³)")


class Alert(BaseModel):
    is_alert: bool = Field(description="Tahmin ≥ istasyonun karar eşiği")
    decision_threshold: float = Field(description="İstasyon karar eşiği (µg/m³), Faz 4.4")
    official_threshold: float = Field(description="Resmî uyarı eşiği: 35,5 µg/m³")
    risk: bool = Field(description="%80 aralığın üst sınırı ≥ 35,5 (uyarı riski)")


class Contribution(BaseModel):
    feature: str
    family: str
    value: float | None
    contribution: float = Field(description="Tahmine katkı (µg/m³); + artırır, − azaltır")


class Explanation(BaseModel):
    base_value: float = Field(description="Modelin ortalama tahmini (taban)")
    top_features: list[Contribution]
    other_features: float = Field(description="Kalan özelliklerin toplam katkısı")


class Measurement(BaseModel):
    time: datetime | None
    pm25: float | None


class ModelInfo(BaseModel):
    name: str
    created: str
    trained_on: str


class Forecast(BaseModel):
    station: str
    station_name: str
    city: str
    issued_at: datetime = Field(description="Tahminin verildiği saat (yerel)")
    target_time: datetime = Field(description="Tahmin edilen saat (yerel), issued_at + 24 s")
    pm25: float = Field(description="24 saat sonrası PM2.5 tahmini (µg/m³)")
    interval_80: Interval
    aqi: int
    category: str
    alert: Alert
    explanation: Explanation
    latest_measurement: Measurement
    model: ModelInfo


class StationError(BaseModel):
    station: str
    error: str


class Station(BaseModel):
    slug: str
    name: str
    city: str
    lat: float
    lon: float
    area_type: str
    source_type: str
    decision_threshold: float


class Health(BaseModel):
    status: str
    model_loaded: bool
    model_created: str | None = None
    stations: int = 0
    detail: str | None = None
