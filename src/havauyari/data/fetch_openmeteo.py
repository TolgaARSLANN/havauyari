"""Open-Meteo'dan saatlik hava kalitesi ve meteoroloji verisini çeker.

Kullanım:
    python -m havauyari.data.fetch_openmeteo                # tüm şehirler
    python -m havauyari.data.fetch_openmeteo --city ankara --force

Her şehir için data/raw/<city>.parquet dosyası oluşturulur. Dosya zaten varsa
(--force verilmedikçe) tekrar indirilmez.
"""

from __future__ import annotations

import argparse
import time
from datetime import date, timedelta

import pandas as pd
import requests

from havauyari.config import CITIES, POLLUTANTS, RAW_DIR, START_DATE, TIMEZONE, WEATHER_VARS, City

AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def _get_hourly(url: str, params: dict, retries: int = 3) -> pd.DataFrame:
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            break
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(2**attempt)
    hourly = resp.json()["hourly"]
    df = pd.DataFrame(hourly)
    df["time"] = pd.to_datetime(df["time"])
    return df.set_index("time")


def fetch_city(city: City, start: str = START_DATE, end: str | None = None) -> pd.DataFrame:
    """Bir şehir için kirletici + hava durumu verisini saatlik tek tabloda birleştirir."""
    # Arşiv API'si birkaç gün gecikmeli güncellenir, bu yüzden bitişi 5 gün geriden alıyoruz.
    end = end or (date.today() - timedelta(days=5)).isoformat()
    common = {
        "latitude": city.lat,
        "longitude": city.lon,
        "start_date": start,
        "end_date": end,
        "timezone": TIMEZONE,
    }
    aq = _get_hourly(AIR_QUALITY_URL, {**common, "hourly": ",".join(POLLUTANTS)})
    wx = _get_hourly(WEATHER_ARCHIVE_URL, {**common, "hourly": ",".join(WEATHER_VARS)})
    df = aq.join(wx, how="outer")
    df.insert(0, "city", city.name)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city", choices=sorted(CITIES), help="Tek şehir indir")
    parser.add_argument("--start", default=START_DATE)
    parser.add_argument("--end", default=None)
    parser.add_argument("--force", action="store_true", help="Var olan dosyanın üzerine yaz")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cities = [CITIES[args.city]] if args.city else CITIES.values()
    for city in cities:
        out = RAW_DIR / f"{city.name}.parquet"
        if out.exists() and not args.force:
            print(f"[atla] {out.name} zaten var")
            continue
        df = fetch_city(city, args.start, args.end)
        df.to_parquet(out)
        print(f"[ok] {city.name}: {len(df):,} satır -> {out}")


if __name__ == "__main__":
    main()
