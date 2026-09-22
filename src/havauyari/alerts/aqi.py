"""PM2.5 konsantrasyonunu (µg/m³) AQI değerine ve kategorisine çevirir.

Eşikler: US EPA, 2024 güncellemesi (PM2.5 NAAQS revizyonu).
Not: Resmi AQI 24 saatlik ortalama üzerinden hesaplanır; saatlik değerler için
bu dönüşüm yaklaşık bir göstergedir.
"""

from __future__ import annotations

import math

# (C_low, C_high, I_low, I_high, kategori)
PM25_BREAKPOINTS: list[tuple[float, float, int, int, str]] = [
    (0.0, 9.0, 0, 50, "İyi"),
    (9.1, 35.4, 51, 100, "Orta"),
    (35.5, 55.4, 101, 150, "Hassas gruplar için sağlıksız"),
    (55.5, 125.4, 151, 200, "Sağlıksız"),
    (125.5, 225.4, 201, 300, "Çok sağlıksız"),
    (225.5, 325.4, 301, 500, "Tehlikeli"),
]

CATEGORIES = [bp[4] for bp in PM25_BREAKPOINTS]
UNHEALTHY_INDEX = CATEGORIES.index("Sağlıksız")


def pm25_to_aqi(conc: float) -> int:
    """EPA doğrusal interpolasyon formülü. Konsantrasyon 0.1'e aşağı yuvarlanır."""
    if conc is None or math.isnan(conc) or conc < 0:
        raise ValueError(f"Geçersiz konsantrasyon: {conc}")
    c = math.floor(conc * 10) / 10
    for c_lo, c_hi, i_lo, i_hi, _ in PM25_BREAKPOINTS:
        if c <= c_hi:
            return round((i_hi - i_lo) / (c_hi - c_lo) * (c - c_lo) + i_lo)
    return 500


def aqi_category(conc: float) -> str:
    c = math.floor(conc * 10) / 10
    for _c_lo, c_hi, *_, name in PM25_BREAKPOINTS:
        if c <= c_hi:
            return name
    return CATEGORIES[-1]


def category_index(conc: float) -> int:
    return CATEGORIES.index(aqi_category(conc))


def is_alert(conc: float, threshold_index: int = UNHEALTHY_INDEX) -> bool:
    """Tahmin edilen değer eşik kategorisine veya üstüne çıkıyorsa uyarı üret."""
    return category_index(conc) >= threshold_index
