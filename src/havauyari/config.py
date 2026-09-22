"""Proje genelinde kullanılan sabitler ve yollar."""

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = ROOT / "models"

TIMEZONE = "Europe/Istanbul"
START_DATE = "2023-01-01"

TARGET = "pm2_5"
POLLUTANTS = ["pm2_5", "pm10", "nitrogen_dioxide", "ozone", "carbon_monoxide", "sulphur_dioxide"]
WEATHER_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
    "precipitation",
]


@dataclass(frozen=True)
class City:
    name: str
    lat: float
    lon: float


CITIES: dict[str, City] = {
    c.name: c
    for c in [
        City("istanbul", 41.0082, 28.9784),
        City("ankara", 39.9334, 32.8597),
        City("izmir", 38.4237, 27.1428),
        City("bursa", 40.1885, 29.0610),
        City("kocaeli", 40.7654, 29.9408),
    ]
}
