"""İstasyon hedefli veri seti: SİM ölçümü (hedef) + istasyon koordinatındaki CAMS ve ERA5.

Kullanım:
    python -m havauyari.data.stations       # -> data/processed/stations.parquet
                                            #    reports/istasyon_veri_kalitesi.md

Temizlik kuralları (gerekçeler: docs/YOL_HARITASI.md, Faz 3.7):
1. PM2.5 ≤ 0 -> NaN (cihaz alt sınırı / hatalı kayıt)
2. Aynı değerin ≥ 6 saat tekrarı -> NaN (takılı sensör)
3. Tek saatlik sıçrama: > 80 µg/m³ ve iki komşusunun da 3 katından büyük -> NaN
4. Hedef (istasyon PM2.5) İNTERPOLE EDİLMEZ: modele yalnızca gerçekten ölçülmüş saatler
   hedef olarak girer. Boşluk doldurma yalnızca özellik üretiminde (≤ 3 saat) yapılır.
5. PM2.5 > PM10 durumları düzeltilmez: iki farklı cihazın ölçümü, kalite raporunda sayılır.

Zaman damgaları: SİM yerel saat (Europe/Istanbul) kullanır. Ozon zirvesi testi (Ankara
istasyonunda 13.00, CAMS'ta 13.00) saatlerin doğru olduğunu gösterdi; istasyon ile CAMS arasındaki
1–7 saatlik kayma CAMS'ın zamanlamasından/yerel süreçlerden kaynaklanıyor ve model tarafından
(CAMS'ın hedef öncesi saatleri özellik olarak verilerek) öğrenilecek.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from havauyari.config import PROCESSED_DIR, RAW_DIR, ROOT, City
from havauyari.data.clean import clean as clean_openmeteo
from havauyari.data.fetch_forecasts import FORECAST_VARS, forecast_column, station_forecasts
from havauyari.data.fetch_openmeteo import fetch_city
from havauyari.data.fetch_sim import SIM_DIR, SURVEY_PATH, select_stations, slugify
from havauyari.reporting import to_markdown

STATION_WX_DIR = RAW_DIR / "openmeteo_stations"
STATIONS_PATH = PROCESSED_DIR / "stations.parquet"
REPORT_PATH = ROOT / "reports" / "istasyon_veri_kalitesi.md"

FLATLINE_HOURS = 6
SPIKE_MIN, SPIKE_RATIO = 80.0, 3.0


# ---------------------------------------------------------------------------------------------
# Temizlik
# ---------------------------------------------------------------------------------------------
def flatline_mask(s: pd.Series, min_hours: int = FLATLINE_HOURS) -> pd.Series:
    """Aynı (NaN olmayan) değerin en az `min_hours` saat üst üste tekrarlandığı saatler."""
    run_id = (s != s.shift()).cumsum()
    run_len = s.groupby(run_id).transform("size")
    return s.notna() & (run_len >= min_hours)


def spike_mask(s: pd.Series, min_value: float = SPIKE_MIN, ratio: float = SPIKE_RATIO) -> pd.Series:
    """Tek saatlik sıçramalar: iki komşunun da `ratio` katından büyük ve `min_value` üstü."""
    return (s > min_value) & (s > ratio * s.shift(1)) & (s > ratio * s.shift(-1))


def clean_station(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """SİM saatlik tablosunu (PM25, PM10) temizler. Dönüş: (tablo, düzeltme sayıları)."""
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="first")].asfreq("h")
    pm = df["PM25"].copy()
    log = {"ölçüm_saati": int(pm.notna().sum())}

    nonpos = pm <= 0
    log["≤0"] = int(nonpos.sum())
    pm[nonpos] = np.nan

    flat = flatline_mask(pm)
    log["takılı_sensör"] = int(flat.sum())
    pm[flat] = np.nan

    spk = spike_mask(pm)
    log["tek_sıçrama"] = int(spk.sum())
    pm[spk] = np.nan

    log["pm25>pm10"] = int((pm > df["PM10"]).sum())
    log["kalan_ölçüm"] = int(pm.notna().sum())
    df["PM25"] = pm
    df.loc[df["PM10"] <= 0, "PM10"] = np.nan
    return df, log


# ---------------------------------------------------------------------------------------------
# İstasyon koordinatlarında CAMS + ERA5
# ---------------------------------------------------------------------------------------------
def station_openmeteo(station: pd.Series, force: bool = False) -> pd.DataFrame:
    """İstasyon koordinatındaki CAMS kirletici ve ERA5 meteoroloji verisi (önbellekli)."""
    STATION_WX_DIR.mkdir(parents=True, exist_ok=True)
    path = STATION_WX_DIR / f"{slugify(station['name'])}.parquet"
    if path.exists() and not force:
        return pd.read_parquet(path)
    raw = fetch_city(City(slugify(station["name"]), station["lat"], station["lon"]))
    raw.to_parquet(path)
    return raw


# ---------------------------------------------------------------------------------------------
# Birleştirme
# ---------------------------------------------------------------------------------------------
def build_dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Seçili istasyonlar için uzun biçimli veri seti ve temizlik özeti."""
    selected = select_stations(pd.read_csv(SURVEY_PATH))
    frames, logs = [], {}
    for _, st in selected.iterrows():
        slug = slugify(st["name"])
        sim, log = clean_station(pd.read_parquet(SIM_DIR / f"{st['city']}__{slug}.parquet"))
        om, _ = clean_openmeteo(station_openmeteo(st))
        om = om.drop(columns="city")
        # Ortak zaman aralığı: Open-Meteo arşivi birkaç gün geriden gelir
        df = om.join(sim.rename(columns={"PM25": "station_pm25", "PM10": "station_pm10"}),
                     how="inner")
        # Geçmişte yayımlanmış day1 hava tahminleri (geçerlilik zamanına göre)
        df = df.join(station_forecasts(st), how="left")
        df.insert(0, "city", st["city"])
        df.insert(0, "station", slug)
        frames.append(df)
        logs[st["name"]] = {**log, "saat_aralığı": len(df),
                            "hedef_dolu_%": df["station_pm25"].notna().mean() * 100}
    data = pd.concat(frames)
    data["station"] = data["station"].astype("category")
    data["city"] = data["city"].astype("category")
    return data, pd.DataFrame(logs).T


def _lag_scan(target: pd.Series, cams: pd.Series, lags=range(-12, 13)) -> tuple[int, float, float]:
    corr = {k: target.corr(cams.shift(k)) for k in lags}
    best = max(corr, key=corr.get)
    return best, corr[best], corr[0]


def _mean_station_corr(d: pd.DataFrame, a: str, b: str, lag: int) -> float:
    """İstasyon başına corr(a, b'nin `lag` saat kaydırılmışı) ortalaması.

    Kaydırma her istasyonun kesintisiz saatlik serisi üzerinde yapılır (boşluklar atılmadan).
    """
    return float(np.mean([g[a].corr(g[b].shift(lag))
                          for _, g in d.groupby("station", observed=True)]))


def forecast_skill(data: pd.DataFrame) -> pd.DataFrame:
    """Day1 tahminlerinin gerçekleşen ERA5 değerine göre hatası (2024-02 sonrası, tüm istasyonlar).

    Gecikme taraması en iyi eşleşmenin 0 saatte olduğunu (zaman hizası doğru) göstermeli.
    """
    d = data[data.index >= "2024-02-01"]
    rows = {}
    for var in FORECAST_VARS:
        fc = forecast_column(var)
        if var not in d or fc not in d or var == "wind_direction_10m":
            continue
        pairs = d[[var, fc, "station"]].dropna()
        lag_r = {k: _mean_station_corr(d, var, fc, k) for k in range(-3, 4)}
        rows[var] = {"MAE": (pairs[fc] - pairs[var]).abs().mean(),
                     "sapma (tahmin - gerçek)": (pairs[fc] - pairs[var]).mean(),
                     "korelasyon": lag_r[0], "en iyi gecikme (s)": max(lag_r, key=lag_r.get),
                     "dolu %": d[fc].notna().mean() * 100}
    out = pd.DataFrame(rows).T
    out["en iyi gecikme (s)"] = out["en iyi gecikme (s)"].astype(int)
    out.index.name = "değişken"
    return out


def build_report(data: pd.DataFrame, cleaning: pd.DataFrame) -> str:
    rows = {}
    for station, g in data.groupby("station", observed=True):
        y, cams = g["station_pm25"], g["pm2_5"]
        both = pd.concat([y, cams], axis=1).dropna()
        lag, r_best, r0 = _lag_scan(y, cams)
        w = g.index.month.isin([12, 1, 2])
        rows[station] = {
            "ort. istasyon": both["station_pm25"].mean(),
            "ort. CAMS": both["pm2_5"].mean(),
            "CAMS/istasyon": both["pm2_5"].mean() / both["station_pm25"].mean(),
            "korelasyon": r0,
            "en iyi gecikme (s)": lag,
            "gecikmeli korelasyon": r_best,
            "kış zirve saati (ist.)": int(y[w].groupby(y[w].index.hour).median().idxmax()),
            "kış zirve saati (CAMS)": int(cams[w].groupby(cams[w].index.hour).median().idxmax()),
            "uyarı saati % (≥35,5)": (y.dropna() >= 35.5).mean() * 100,
        }
    comp = pd.DataFrame(rows).T
    int_cols = ["en iyi gecikme (s)", "kış zirve saati (ist.)", "kış zirve saati (CAMS)"]
    comp[int_cols] = comp[int_cols].astype(int)
    comp.index.name = "istasyon"
    cleaning = cleaning.astype({c: int for c in cleaning.columns if c != "hedef_dolu_%"})
    cleaning.index.name = "istasyon"
    return "\n".join([
        "# İstasyon Veri Kalitesi",
        "",
        f"_Oluşturulma: {date.today().isoformat()} · Kaynak: SİM saatlik ölçüm + istasyon "
        "koordinatında Open-Meteo (CAMS, ERA5) · Üreten: `python -m havauyari.data.stations`_",
        "",
        "## Temizlik",
        "",
        "Kurallar `src/havauyari/data/stations.py` başındadır. Hedef (istasyon PM2.5) interpole "
        "edilmez; yalnızca ölçülmüş saatler hedef olarak kullanılır.",
        "",
        to_markdown(cleaning, ".1f"),
        "",
        "## CAMS (istasyon koordinatında) ile istasyon ölçümü",
        "",
        "Gecikme > 0: istasyon, CAMS'ın k saat önceki değeriyle en iyi eşleşiyor (CAMS erken).",
        "",
        to_markdown(comp, ".2f"),
        "",
        "## Hava tahmini (day1) kalitesi",
        "",
        "Open-Meteo Previous Runs API: geçerlilik anından en az 1 gün önce başlatılmış model "
        "çalıştırması. Karşılaştırma: istasyon koordinatındaki ERA5 değeri, 2024-02 sonrası. "
        "Sıcaklık 2023'ten, diğer değişkenler 2024-01-19'dan itibaren mevcut.",
        "",
        to_markdown(forecast_skill(data), ".2f"),
        "",
        "## Saat hizası kontrolü",
        "",
        "Ozon fotokimyasal olarak öğleden sonra zirve yapar. Temmuz 2025 medyan profilinde "
        "Ankara-Keçiören istasyonunun ozon zirvesi 13.00, CAMS'ınki 13.00; ERA5 sıcaklık zirvesi "
        "13.00–16.00 arası. SİM zaman damgaları yerel saattir ve kaydırma gerekmez. İstasyon ozon "
        "zirvesinin İstanbul/Bursa/Kocaeli'de CAMS'tan 2–4 saat geç olması, PM2.5'teki kaymayla "
        "aynı yönde: CAMS olayları sistematik olarak erken gösteriyor.",
        "",
    ])


def main() -> None:
    data, cleaning = build_dataset()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    data.to_parquet(STATIONS_PATH)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build_report(data, cleaning) + "\n", encoding="utf-8")
    print(cleaning.round(1).to_string())
    print(f"[ok] {len(data):,} satır, {data['station'].nunique()} istasyon -> {STATIONS_PATH}")
    print(f"[ok] {REPORT_PATH}")


if __name__ == "__main__":
    main()
