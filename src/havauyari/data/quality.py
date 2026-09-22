"""Ham veri için kalite raporu üretir.

Kullanım:
    python -m havauyari.data.quality      # -> reports/veri_kalite_raporu.md

Kontroller: kapsam, eksik değer, fiziksel sınırlar, PM2.5 <= PM10 tutarlılığı, sabit kalan
(takılı) değerler, ani sıçramalar (robust z-skoru), aylık dağılım, şehirler arası korelasyon ve
AQI seviyelerinin görülme oranları.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from havauyari.alerts.aqi import PM25_BREAKPOINTS
from havauyari.config import PHYSICAL_LIMITS, RAW_DIR, ROOT, TARGET
from havauyari.reporting import to_markdown as _md

REPORT_PATH = ROOT / "reports" / "veri_kalite_raporu.md"

# Değişmemesi normal olan değişkenler (yağış çoğu saat 0'dır)
FLATLINE_EXEMPT = {"precipitation"}

MONTHS_TR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]


def load_raw() -> dict[str, pd.DataFrame]:
    frames = {p.stem: pd.read_parquet(p) for p in sorted(RAW_DIR.glob("*.parquet"))}
    if not frames:
        raise FileNotFoundError(f"{RAW_DIR} boş. Önce fetch_openmeteo çalıştırın.")
    return frames


def coverage(df: pd.DataFrame) -> dict:
    idx = df.index
    expected = pd.date_range(idx.min(), idx.max(), freq="h")
    return {
        "başlangıç": idx.min(),
        "bitiş": idx.max(),
        "satır": len(df),
        "beklenen": len(expected),
        "tekrar": int(idx.duplicated().sum()),
        "eksik saat": len(expected.difference(idx)),
    }


def out_of_range(df: pd.DataFrame) -> pd.Series:
    counts = {}
    for col, (lo, hi) in PHYSICAL_LIMITS.items():
        if col in df:
            counts[col] = int(((df[col] < lo) | (df[col] > hi)).sum())
    return pd.Series(counts)


def pm25_gt_pm10(df: pd.DataFrame, tol: float = 0.1) -> int:
    """PM2.5 fiziksel olarak PM10'un alt kümesidir; PM2.5 > PM10 ise veri tutarsızdır."""
    return int((df["pm2_5"] > df["pm10"] + tol).sum())


def flatline_runs(s: pd.Series, min_hours: int = 6) -> tuple[int, int]:
    """En az `min_hours` saat boyunca hiç değişmeyen seriler (takılı sensör/model belirtisi).

    Dönüş: (koşu sayısı, en uzun koşu saat cinsinden)
    """
    s = s.dropna()
    if s.empty:
        return 0, 0
    run_id = (s != s.shift()).cumsum()
    lengths = s.groupby(run_id).size()
    long = lengths[lengths >= min_hours]
    return int(len(long)), int(lengths.max())


def spikes(s: pd.Series, window: int = 24 * 7, z: float = 6.0) -> int:
    """Kayan medyan/MAD tabanlı robust z-skoru eşiği aşan saat sayısı."""
    med = s.rolling(window, center=True, min_periods=window // 2).median()
    mad = (s - med).abs().rolling(window, center=True, min_periods=window // 2).median()
    rz = 0.6745 * (s - med) / mad.replace(0, np.nan)
    return int((rz.abs() > z).sum())


def aqi_level_rates(s: pd.Series) -> pd.Series:
    rates = {}
    for c_lo, _c_hi, _i_lo, _i_hi, name in PM25_BREAKPOINTS[1:]:
        rates[f"≥{c_lo} ({name})"] = (s >= c_lo).mean() * 100
    return pd.Series(rates)


def _per_city(frames: dict[str, pd.DataFrame], fn, index_name: str = "şehir") -> pd.DataFrame:
    """Her şehrin PM2.5 serisine `fn` uygular, sonuçları şehir satırlarında birleştirir."""
    out = pd.DataFrame({c: fn(df[TARGET]) for c, df in frames.items()}).T
    out.index.name = index_name
    return out


def build_report(frames: dict[str, pd.DataFrame]) -> str:
    cities = list(frames)
    num_cols = [c for c in frames[cities[0]].columns if c != "city"]
    out: list[str] = [
        "# Veri Kalite Raporu",
        "",
        f"_Oluşturulma: {date.today().isoformat()} · Kaynak: `data/raw/*.parquet` "
        "(Open-Meteo, CAMS + ERA5) · Üreten: `python -m havauyari.data.quality`_",
        "",
    ]

    # 1. Kapsam
    cov = pd.DataFrame({c: coverage(df) for c, df in frames.items()}).T
    cov.index.name = "şehir"
    out += ["## 1. Kapsam", "", _md(cov), ""]

    # 2. Eksik değer
    miss = pd.DataFrame({c: df[num_cols].isna().mean() * 100 for c, df in frames.items()})
    miss.index.name = "değişken (% boş)"
    out += ["## 2. Eksik değer oranı (%)", "", _md(miss, ".2f"), ""]

    # 3. Fiziksel sınır dışı değerler
    oor = pd.DataFrame({c: out_of_range(df) for c, df in frames.items()})
    oor.index.name = "değişken"
    out += ["## 3. Fiziksel sınır dışı değer sayısı", "",
            "Sınırlar `PHYSICAL_LIMITS` sözlüğünde tanımlıdır.", "", _md(oor), ""]

    # 4. Tutarlılık ve anomaliler
    rows = {}
    for c, df in frames.items():
        runs, longest = flatline_runs(df[TARGET])
        rows[c] = {
            "PM2.5 > PM10": pm25_gt_pm10(df),
            "PM2.5 sabit koşu (≥6s)": runs,
            "PM2.5 en uzun sabit koşu (s)": longest,
            "PM2.5 sıçrama (robust z > 6)": spikes(df[TARGET]),
        }
    anom = pd.DataFrame(rows).T
    anom.index.name = "şehir"
    flat_other = {}
    for c, df in frames.items():
        for col in num_cols:
            if col in FLATLINE_EXEMPT or col == TARGET:
                continue
            n, longest = flatline_runs(df[col], min_hours=12)
            if n:
                flat_other[(c, col)] = {"koşu (≥12s)": n, "en uzun (s)": longest}
    out += ["## 4. Tutarlılık ve anomaliler", "", _md(anom), ""]
    if flat_other:
        fo = pd.DataFrame(flat_other).T
        fo.index = [f"{a} / {b}" for a, b in fo.index]
        fo.index.name = "şehir / değişken"
        out += ["Diğer değişkenlerde 12 saat ve üzeri değişmeyen koşular:", "", _md(fo), ""]
    else:
        out += ["Diğer değişkenlerde 12 saat ve üzeri değişmeyen koşu yok.", ""]

    # 5. PM2.5 dağılımı
    desc = _per_city(frames, lambda s: s.describe(percentiles=[0.5, 0.9, 0.99]))
    desc = desc.drop(columns="count")
    out += ["## 5. PM2.5 dağılımı (µg/m³)", "", _md(desc), ""]

    monthly = _per_city(frames, lambda s: s.groupby(s.index.month).median())
    monthly.columns = MONTHS_TR
    out += ["### Aylık medyan PM2.5 (µg/m³)", "", _md(monthly), ""]

    hourly = _per_city(frames, lambda s: s.groupby(s.index.hour).median())
    hourly = hourly[[0, 3, 6, 9, 12, 15, 18, 21]]
    hourly.columns = [f"{h:02d}:00" for h in hourly.columns]
    out += ["### Saate göre medyan PM2.5 (µg/m³)", "", _md(hourly), ""]

    yearly = _per_city(frames, lambda s: s.groupby(s.index.year).mean())
    yearly.columns = [str(y) for y in yearly.columns]
    out += ["### Yıllık ortalama PM2.5 (µg/m³)", "",
            "Son yıl kısmi olduğu için (Eylül'e kadar) kış ayları eksik ve ortalama düşük görünür.",
            "", _md(yearly), ""]

    # 6. AQI seviyeleri
    lv = _per_city(frames, aqi_level_rates, "şehir (% saat)")
    out += ["## 6. AQI seviyelerinin görülme oranı (% saat)", "", _md(lv, ".2f"), ""]

    # 7. Şehirler arası korelasyon
    daily = pd.DataFrame({c: df[TARGET].resample("D").mean() for c, df in frames.items()})
    corr = daily.corr()
    corr.index.name = "günlük PM2.5"
    out += ["## 7. Şehirler arası korelasyon (günlük ortalama PM2.5)", "", _md(corr, ".2f"), ""]

    return "\n".join(out)


def main() -> None:
    report = build_report(load_raw())
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report + "\n", encoding="utf-8")
    print(f"[ok] {REPORT_PATH}")


if __name__ == "__main__":
    main()
