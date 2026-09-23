"""API yanıt şemaları (Pydantic). FastAPI bunlardan /docs sayfasını otomatik üretir."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Interval(BaseModel):
    low: float = Field(description="%80'lik aralığın alt sınırı (µg/m³)")
    high: float = Field(description="%80'lik aralığın üst sınırı (µg/m³)")


class Alert(BaseModel):
    is_alert: bool = Field(description="Tahmin, istasyonun karar eşiğine eşit ya da ondan büyük")
    decision_threshold: float = Field(description="İstasyonun uyarı karar eşiği (µg/m³)")
    official_threshold: float = Field(description="Resmî uyarı eşiği: 35,5 µg/m³")
    risk: bool = Field(description="Uyarı riski: %80'lik aralığın üst sınırı 35,5 µg/m³'e "
                                   "eşit ya da ondan büyük")


class Contribution(BaseModel):
    feature: str
    family: str
    value: float | None
    contribution: float = Field(description="Tahmine katkı (µg/m³); artı değer tahmini "
                                            "yükseltir, eksi değer düşürür")


class Explanation(BaseModel):
    base_value: float = Field(description="Modelin ortalama tahmini (taban değer)")
    top_features: list[Contribution]
    other_features: float = Field(description="Diğer özelliklerin toplam katkısı")


class Measurement(BaseModel):
    time: datetime | None
    pm25: float | None


class ModelInfo(BaseModel):
    name: str
    created: str
    trained_on: str


class TrajectoryPoint(BaseModel):
    issued_at: datetime
    target_time: datetime
    pm25: float
    low: float
    high: float
    actual: float | None = Field(description="Gerçekleşen ölçüm (henüz ölçülmediyse null)")


class HistoryPoint(BaseModel):
    time: datetime
    pm25: float | None


class Forecast(BaseModel):
    station: str
    station_name: str
    city: str
    issued_at: datetime = Field(description="Tahminin verildiği saat (yerel saat)")
    target_time: datetime = Field(description="Tahmin edilen saat (yerel saat): "
                                              "issued_at + 24 saat")
    pm25: float = Field(description="24 saat sonrası için PM2.5 tahmini (µg/m³)")
    interval_80: Interval
    aqi: int
    category: str
    alert: Alert
    explanation: Explanation
    latest_measurement: Measurement
    model: ModelInfo
    trajectory: list[TrajectoryPoint] = Field(
        description="Son 96 saatte her saat verilmiş 24 saatlik tahminler; son 24 tahmin, "
                    "önümüzdeki 24 saati kapsar")
    history: list[HistoryPoint] = Field(description="Son 72 saatin istasyon ölçümleri")


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
