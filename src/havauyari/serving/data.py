"""Canlı veri sağlayıcı: eğitimdeki istasyon veri setiyle AYNI sütun yapısında ham tablo üretir.

Sütunlar (data.stations.build_dataset ile aynı):
    station, city, <CAMS kirleticileri>, <meteoroloji>, station_pm25, station_pm10, fc_<değişken>

Kaynaklar:
- İstasyon: SİM, son `HISTORY_DAYS` gün (eğitimle aynı kaynak)
- CAMS: Open-Meteo Air Quality API, geçmiş + tahmin (eğitimle aynı kaynak)
- Meteoroloji: Open-Meteo Forecast API'nin geçmiş günleri. Eğitimde ERA5 arşivi kullanıldı
  (arşiv ~5 gün gecikmeli olduğu için canlıda kullanılamaz): küçük bir kaynak farkı.
- 1 gün önce yayımlanan hava tahmini: Previous Runs API (eğitimle birebir aynı)
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Protocol

import pandas as pd

from havauyari.config import POLLUTANTS, TIMEZONE, WEATHER_VARS
from havauyari.data.fetch_forecasts import FORECAST_VARS, PREVIOUS_RUNS_URL, forecast_column
from havauyari.data.fetch_openmeteo import AIR_QUALITY_URL, _get_hourly
from havauyari.data.fetch_sim import SimClient

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HISTORY_DAYS = 10          # lag168 + rollmean168 için ≥ 8 gün gerekir
FORECAST_DAYS = 2


class DataProvider(Protocol):
    def station_frame(self, station: dict, now: datetime) -> pd.DataFrame:
        """`now` (yerel saat, saat başı) dahil geçmişi ve tahmin penceresini içeren ham tablo."""


class LiveProvider:
    def __init__(self, sim_client: SimClient | None = None):
        self.sim = sim_client or SimClient(pause_s=0.5)

    def station_frame(self, station: dict, now: datetime) -> pd.DataFrame:
        base = {"latitude": station["lat"], "longitude": station["lon"], "timezone": TIMEZONE}
        window = {"past_days": HISTORY_DAYS, "forecast_days": FORECAST_DAYS}
        cams = _get_hourly(AIR_QUALITY_URL, {**base, **window, "hourly": ",".join(POLLUTANTS)})
        wx = _get_hourly(FORECAST_URL, {**base, **window, "hourly": ",".join(WEATHER_VARS)})
        start = (now - timedelta(days=HISTORY_DAYS)).date().isoformat()
        end = (now + timedelta(days=FORECAST_DAYS)).date().isoformat()
        fc = _get_hourly(PREVIOUS_RUNS_URL, {
            **base, "start_date": start, "end_date": end,
            "hourly": ",".join(f"{v}_previous_day1" for v in FORECAST_VARS)})
        fc.columns = [forecast_column(c.removesuffix("_previous_day1")) for c in fc.columns]

        sim = self.sim.measurements([station["sim_id"]], now - timedelta(days=HISTORY_DAYS),
                                    now + timedelta(hours=1))
        sim = (sim.set_index("time")[["PM25", "PM10"]]
                  .rename(columns={"PM25": "station_pm25", "PM10": "station_pm10"}))
        return assemble(station, cams, wx, sim, fc)


def assemble(station: dict, cams: pd.DataFrame, wx: pd.DataFrame, sim: pd.DataFrame,
             fc: pd.DataFrame) -> pd.DataFrame:
    """Kaynakları saatlik tek tabloda birleştirir (eksik saatler NaN olarak kalır)."""
    idx = cams.index.union(wx.index).union(fc.index)
    idx = pd.date_range(idx.min(), idx.max(), freq="h")
    df = pd.DataFrame(index=idx)
    df = df.join(cams[POLLUTANTS]).join(wx[WEATHER_VARS]).join(sim, how="left").join(fc)
    df.insert(0, "city", station["city"])
    df.insert(0, "station", station["slug"])
    df.index.name = "time"
    return df.apply(lambda s: pd.to_numeric(s, errors="coerce") if s.name not in
                    ("station", "city") else s)
