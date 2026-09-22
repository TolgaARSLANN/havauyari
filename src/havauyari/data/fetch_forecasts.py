"""Geçmişte yayımlanmış hava tahminleri (Open-Meteo Previous Runs API).

`<değişken>_previous_day1`, geçerlilik anından en az 1 gün önce başlatılmış model çalıştırmasının
tahminidir. Bu yüzden t anında, geçerlilik zamanı t…t+24 olan day1 tahminleri zaten yayımlanmıştır
ve özellik olarak kullanılabilir (features.build.add_weather_forecast bu sınırı zorunlu kılar).

Arşiv 2024 başından itibaren tam; 2023'te yalnızca sıcaklık var (Faz 3.5 yoklaması). Bu yüzden
tahmin özellikleri 2024-01-01'den itibaren doludur.

Kullanım:
    python -m havauyari.data.fetch_forecasts      # seçili istasyonların koordinatları için
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from havauyari.config import RAW_DIR, START_DATE, TIMEZONE
from havauyari.data.fetch_openmeteo import _get_hourly

PREVIOUS_RUNS_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
FORECAST_VARS = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m",
                 "wind_direction_10m", "precipitation", "surface_pressure", "cloud_cover"]
FORECAST_DAY = 1
FORECAST_DIR = RAW_DIR / "forecasts"


def forecast_column(var: str) -> str:
    return f"fc_{var}"


def fetch_previous_runs(lat: float, lon: float, start: str = START_DATE,
                        end: str | None = None, day: int = FORECAST_DAY) -> pd.DataFrame:
    """Geçerlilik zamanına göre indeksli `fc_<değişken>` tablosu (yıllık parçalarla)."""
    end = end or date.today().isoformat()
    parts = []
    for y0, y1 in _year_chunks(start, end):
        hourly = ",".join(f"{v}_previous_day{day}" for v in FORECAST_VARS)
        part = _get_hourly(PREVIOUS_RUNS_URL, {"latitude": lat, "longitude": lon,
                                               "start_date": y0, "end_date": y1,
                                               "timezone": TIMEZONE, "hourly": hourly})
        parts.append(part)
    df = pd.concat(parts)
    df = df[~df.index.duplicated(keep="first")].sort_index()
    df.columns = [forecast_column(c.removesuffix(f"_previous_day{day}")) for c in df.columns]
    return df.apply(pd.to_numeric, errors="coerce")


def _year_chunks(start: str, end: str):
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    while s <= e:
        chunk_end = min(pd.Timestamp(year=s.year, month=12, day=31), e)
        yield s.date().isoformat(), chunk_end.date().isoformat()
        s = chunk_end + pd.Timedelta(days=1)


def station_forecasts(station: pd.Series, force: bool = False) -> pd.DataFrame:
    """İstasyon koordinatı için day1 tahminleri (önbellekli)."""
    from havauyari.data.fetch_sim import slugify

    FORECAST_DIR.mkdir(parents=True, exist_ok=True)
    path = FORECAST_DIR / f"{slugify(station['name'])}.parquet"
    if path.exists() and not force:
        return pd.read_parquet(path)
    df = fetch_previous_runs(station["lat"], station["lon"])
    df.to_parquet(path)
    return df


def main() -> None:
    from havauyari.data.fetch_sim import SURVEY_PATH, select_stations

    for _, st in select_stations(pd.read_csv(SURVEY_PATH)).iterrows():
        df = station_forecasts(st, force=True)
        filled = df.notna().mean().mul(100).round(1).to_dict()
        first = {c: str(df[c].first_valid_index())[:10] for c in df.columns}
        print(f"[ok] {st['name']}: {len(df):,} saat")
        print(f"     dolu %: {filled}")
        print(f"     ilk dolu: {first}")


if __name__ == "__main__":
    main()
