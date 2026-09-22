"""Zaman serisi özellikleri.

İki tür özellik vardır:

1. **Gözlem özellikleri:** t satırında yalnızca t ve öncesindeki ölçümler kullanılır
   (PM2.5 geçmişi, diğer kirleticiler, meteoroloji).
2. **Hedef zamanı özellikleri** (`tgt_` önekli): tahmin edilen an t+h'nin takvimi (saat, gün,
   tatil) önceden bilinir; ölçüm içermediği için sızıntı değildir. Bunlara ek olarak hedef saatle
   hizalı geçmiş PM2.5 değerleri (1 gün / 1 hafta önce aynı saat) de t anında bilinir.

Hedef `target_h{h}`, t+h anındaki PM2.5 değeridir (direkt çok-ufuklu strateji: her ufuk için
ayrı model). Özellik seçimlerinin gerekçeleri: notebooks/01_eda.ipynb, 12. bölüm.
"""

from __future__ import annotations

from functools import lru_cache

import holidays
import numpy as np
import pandas as pd

from havauyari.config import TARGET
from havauyari.data.fetch_forecasts import FORECAST_DAY

# --- PM2.5 geçmişi (Faz 2.1) -------------------------------------------------------------------
# ACF: lag 1 ≈ 0,96, 12 saatte ~0,45'e düşüyor, 24 ve 168 saatte yeniden yükseliyor.
LAGS = [1, 2, 3, 6, 12, 24, 48, 168]
ROLL_WINDOWS = [6, 24, 168]

# --- Diğer kirleticiler (Faz 2.3) --------------------------------------------------------------
# PM2.5 ile Spearman ρ: PM10 0,96 · SO₂ 0,75 · NO₂ 0,74 · CO 0,72 · O₃ −0,59
OTHER_POLLUTANTS = ["pm10", "nitrogen_dioxide", "sulphur_dioxide", "carbon_monoxide", "ozone"]
POLLUTANT_LAGS = [1, 24]
POLLUTANT_ROLL = 24

# --- Meteoroloji (Faz 2.3) ---------------------------------------------------------------------
CALM_WIND_KMH = 4.0  # ~1 m/s; EDA'da en kirli rüzgâr sınıfı 0–2 km/sa
HEATING_BASE_C = 15.0  # ısıtma derece-saati tabanı
PRECIP_WINDOWS = [3, 6, 24]


# ---------------------------------------------------------------------------------------------
# Takvim ve tatiller (Faz 2.2)
# ---------------------------------------------------------------------------------------------
@lru_cache(maxsize=16)
def _holiday_dates(first_year: int, last_year: int) -> frozenset:
    return frozenset(holidays.Turkey(years=range(first_year, last_year + 1)))


def is_holiday(idx: pd.DatetimeIndex) -> np.ndarray:
    """Türkiye resmî tatili (dinî bayramlar dahil) olan günler için 1.

    Not: arefe yarım günleri ve sonradan ilan edilen köprü tatilleri dahil değildir.
    """
    if len(idx) == 0:
        return np.zeros(0, dtype=int)
    days = _holiday_dates(idx.min().year, idx.max().year)
    return pd.Index(idx.date).isin(days).astype(int)


def add_calendar(df: pd.DataFrame) -> pd.DataFrame:
    idx = df.index
    df["hour"] = idx.hour
    df["dayofweek"] = idx.dayofweek
    df["month"] = idx.month
    df["is_weekend"] = (idx.dayofweek >= 5).astype(int)
    df["is_holiday"] = is_holiday(idx)
    # Döngüsel kodlama: 23 ile 0 saatinin birbirine yakın olduğunu modele söyler
    df["hour_sin"] = np.sin(2 * np.pi * idx.hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * idx.hour / 24)
    df["month_sin"] = np.sin(2 * np.pi * idx.month / 12)
    df["month_cos"] = np.cos(2 * np.pi * idx.month / 12)
    return df


# ---------------------------------------------------------------------------------------------
# PM2.5 geçmişi (Faz 2.1)
# ---------------------------------------------------------------------------------------------
def add_lags(df: pd.DataFrame, col: str = TARGET) -> pd.DataFrame:
    for lag in LAGS:
        df[f"{col}_lag{lag}"] = df[col].shift(lag)
    # shift(1): pencere t-1'e kadarını kapsar; t anındaki değer zaten ham sütunda mevcut
    past = df[col].shift(1)
    for w in ROLL_WINDOWS:
        df[f"{col}_rollmean{w}"] = past.rolling(w, min_periods=w // 2).mean()
        df[f"{col}_rollstd{w}"] = past.rolling(w, min_periods=w // 2).std()
    df[f"{col}_rollmax24"] = past.rolling(24, min_periods=12).max()
    # Eğilim: son 1 / 24 saatte ne kadar değişti
    df[f"{col}_diff1"] = df[col] - df[f"{col}_lag1"]
    df[f"{col}_diff24"] = df[col] - df[f"{col}_lag24"]
    return df


# ---------------------------------------------------------------------------------------------
# Diğer kirleticiler ve meteoroloji (Faz 2.3)
# ---------------------------------------------------------------------------------------------
def add_pollutants(df: pd.DataFrame) -> pd.DataFrame:
    """Diğer kirleticilerin geçmişi. t anındaki değerler ham sütunlarda zaten mevcut."""
    for col in OTHER_POLLUTANTS:
        if col not in df:
            continue
        for lag in POLLUTANT_LAGS:
            df[f"{col}_lag{lag}"] = df[col].shift(lag)
        roll = df[col].rolling(POLLUTANT_ROLL, min_periods=POLLUTANT_ROLL // 2)
        df[f"{col}_rollmean{POLLUTANT_ROLL}"] = roll.mean()
    if {TARGET, "pm10"} <= set(df.columns):
        # İnce/kaba partikül oranı: yüksek oran yanma kaynağına işaret eder (Faz 1.2 bulgusu)
        ratio = df[TARGET] / df["pm10"].where(df["pm10"] > 0)
        df["pm_ratio"] = ratio
        df["pm_ratio_rollmean24"] = ratio.rolling(24, min_periods=12).mean()
    return df


def add_meteorology(df: pd.DataFrame) -> pd.DataFrame:
    cols = set(df.columns)
    if {"wind_speed_10m", "wind_direction_10m"} <= cols:
        ws = df["wind_speed_10m"]
        rad = np.deg2rad(df["wind_direction_10m"])
        df["wind_u"] = ws * np.sin(rad)
        df["wind_v"] = ws * np.cos(rad)
        df["wind_speed_rollmean6"] = ws.rolling(6, min_periods=3).mean()
        df["wind_speed_rollmean24"] = ws.rolling(24, min_periods=12).mean()
        # Yön kalıcılığı: son 24 saatin ortalama rüzgâr vektörü
        df["wind_u_rollmean24"] = df["wind_u"].rolling(24, min_periods=12).mean()
        df["wind_v_rollmean24"] = df["wind_v"].rolling(24, min_periods=12).mean()
        # Durgunluk: son 24 saatte kaç saat rüzgâr neredeyse yoktu
        calm = (ws < CALM_WIND_KMH).astype(float).where(ws.notna())
        df["calm_hours24"] = calm.rolling(24, min_periods=12).sum()
    if "precipitation" in cols:
        for w in PRECIP_WINDOWS:
            df[f"precip_sum{w}"] = df["precipitation"].rolling(w, min_periods=1).sum()
    if "temperature_2m" in cols:
        t = df["temperature_2m"]
        df["heating_degree"] = (HEATING_BASE_C - t).clip(lower=0)
        df["heating_degree_rollmean24"] = df["heating_degree"].rolling(24, min_periods=12).mean()
        # Büyük günlük sıcaklık farkı + durgun hava = kararlı atmosfer (inversiyon eğilimi)
        roll = t.rolling(24, min_periods=12)
        df["temp_range24"] = roll.max() - roll.min()
        df["temp_diff24"] = t - t.shift(24)
    if "surface_pressure" in cols:
        # Basınç yükselişi antisiklon ve durgunluğa işaret edebilir
        df["pressure_diff24"] = df["surface_pressure"] - df["surface_pressure"].shift(24)
    if "relative_humidity_2m" in cols:
        df["humidity_rollmean24"] = df["relative_humidity_2m"].rolling(24, min_periods=12).mean()
    return df


# ---------------------------------------------------------------------------------------------
# Hedef zamanı özellikleri ve hedef
# ---------------------------------------------------------------------------------------------
def add_horizon_features(df: pd.DataFrame, horizon: int, col: str = TARGET) -> pd.DataFrame:
    """Tahmin edilen an (t+h) ile ilgili, t anında bilinen özellikler."""
    tgt = df.index + pd.Timedelta(hours=horizon)
    df["tgt_hour_sin"] = np.sin(2 * np.pi * tgt.hour / 24)
    df["tgt_hour_cos"] = np.cos(2 * np.pi * tgt.hour / 24)
    df["tgt_dayofweek"] = tgt.dayofweek
    df["tgt_is_weekend"] = (tgt.dayofweek >= 5).astype(int)
    df["tgt_is_holiday"] = is_holiday(tgt)
    # Hedef saatle aynı saatteki en son gözlemler: t+h-24k (k ≥ 1 ve t+h-24k ≤ t)
    day_shift = 24 * int(np.ceil(horizon / 24)) - horizon
    df[f"{col}_tgt_day_ago"] = df[col].shift(day_shift)
    if horizon <= 168:
        df[f"{col}_tgt_week_ago"] = df[col].shift(168 - horizon)
    return df


def add_weather_forecast(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Geçmişte yayımlanmış day1 hava tahminlerinden (`fc_<değişken>`, geçerlilik zamanına göre
    indeksli) t anında bilinen özellikler üretir. Faz 3.8.

    Sızıntı kuralı: day1 tahmini geçerlilik anından en az 24 saat önce yayımlanır. t anında yalnızca
    geçerlilik zamanı ≤ t+24 olan tahminler yayımlanmıştır; bu yüzden yalnızca (t, t+h] penceresi
    kullanılır ve h ≤ 24 olmalıdır. Ham `fc_` sütunları özellik olarak bırakılmaz.
    """
    fc_cols = [c for c in df.columns if c.startswith("fc_")]
    if not fc_cols:
        return df
    max_h = 24 * FORECAST_DAY
    if horizon > max_h:
        raise ValueError(f"day{FORECAST_DAY} tahminleri en fazla {max_h} saat ufuk için geçerli "
                         f"(istenen: {horizon}). Daha uzun ufuk için previous_day2+ gerekir.")

    h = horizon

    def at_target(s: pd.Series) -> pd.Series:
        return s.shift(-h)

    def window(s: pd.Series, how: str) -> pd.Series:
        """(t, t+h] penceresinin özeti, t satırına yazılır."""
        return s.rolling(h, min_periods=1).agg(how).shift(-h)

    fc = {c.removeprefix("fc_"): df[c] for c in fc_cols}
    if "temperature_2m" in fc:
        t = fc["temperature_2m"]
        df["fc_tgt_temperature"] = at_target(t)
        df["fc_win_temp_min"] = window(t, "min")
        df["fc_win_temp_range"] = window(t, "max") - df["fc_win_temp_min"]
        if "temperature_2m" in df:
            df["fc_tgt_temp_change"] = df["fc_tgt_temperature"] - df["temperature_2m"]
    if "wind_speed_10m" in fc:
        ws = fc["wind_speed_10m"]
        df["fc_tgt_wind_speed"] = at_target(ws)
        df["fc_win_wind_mean"] = window(ws, "mean")
        df["fc_win_wind_min"] = window(ws, "min")
        calm = (ws < CALM_WIND_KMH).astype(float).where(ws.notna())
        df["fc_win_calm_hours"] = window(calm, "sum")
        if "wind_speed_10m" in df:
            df["fc_tgt_wind_change"] = df["fc_tgt_wind_speed"] - df["wind_speed_10m"]
        if "wind_direction_10m" in fc:
            rad = np.deg2rad(fc["wind_direction_10m"])
            df["fc_tgt_wind_u"] = at_target(ws * np.sin(rad))
            df["fc_tgt_wind_v"] = at_target(ws * np.cos(rad))
    if "precipitation" in fc:
        df["fc_win_precip_sum"] = window(fc["precipitation"], "sum")
    if "relative_humidity_2m" in fc:
        df["fc_tgt_humidity"] = at_target(fc["relative_humidity_2m"])
    if "surface_pressure" in fc:
        df["fc_tgt_pressure"] = at_target(fc["surface_pressure"])
        if "surface_pressure" in df:
            df["fc_tgt_pressure_change"] = df["fc_tgt_pressure"] - df["surface_pressure"]
    if "cloud_cover" in fc:
        df["fc_tgt_cloud_cover"] = at_target(fc["cloud_cover"])
        df["fc_win_cloud_mean"] = window(fc["cloud_cover"], "mean")
    return df.drop(columns=fc_cols)


def add_target(df: pd.DataFrame, horizon: int, col: str = TARGET) -> pd.DataFrame:
    df[f"target_h{horizon}"] = df[col].shift(-horizon)
    return df


def build_features(df: pd.DataFrame, horizon: int = 24, col: str = TARGET) -> pd.DataFrame:
    """Tek şehirlik saatlik tabloya tüm özellikleri ve `target_h{horizon}` hedefini ekler."""
    out = df.copy()
    out = add_calendar(out)
    out = add_lags(out, col)
    out = add_pollutants(out)
    out = add_meteorology(out)
    out = add_horizon_features(out, horizon, col)
    out = add_weather_forecast(out, horizon)
    out = add_target(out, horizon, col)
    return out


def build_all_cities(df: pd.DataFrame, horizon: int = 24) -> pd.DataFrame:
    """Lag'ler şehirler arasında karışmasın diye her şehri ayrı işler."""
    parts = [build_features(g, horizon) for _, g in df.groupby("city", sort=False, observed=True)]
    return pd.concat(parts)


# ---------------------------------------------------------------------------------------------
# İstasyon hedefi (Faz 3.9)
# ---------------------------------------------------------------------------------------------
STATION_TARGET = "station_pm25"
CAMS_COL = "pm2_5"
CAMS_TGT_LAGS = [1, 2, 3, 4, 5, 6]
FEATURE_FFILL_HOURS = 3


def add_cams_forecast(df: pd.DataFrame, horizon: int, col: str = CAMS_COL) -> pd.DataFrame:
    """CAMS'ın hedef anı (t+h) ve öncesindeki değerleri: canlı sistemdeki CAMS tahmininin vekili.

    UYARI (İYİMSER): geçmiş CAMS tahmin arşivi olmadığından CAMS'ın analiz değerleri kullanılır.
    Canlı sistemde bu değerler CAMS'ın 24-48 saatlik tahmininden gelecek ve daha hatalı olacak.
    Bu yüzden bu özelliklerle eğitilen model bir üst sınırdır; `cams_` önekli sütunlar gerçekçi
    modelde kullanılmaz. İstasyonun CAMS'tan 1-6 saat geç tepki vermesi (Faz 3.7) nedeniyle
    hedeften önceki 6 saat de eklenir.
    """
    h = horizon
    s = df[col]
    df["cams_tgt"] = s.shift(-h)
    for k in CAMS_TGT_LAGS:
        if k < h:
            df[f"cams_tgt_lag{k}"] = s.shift(k - h)
    df["cams_win_mean"] = s.rolling(h, min_periods=1).mean().shift(-h)
    df["cams_win_max"] = s.rolling(h, min_periods=1).max().shift(-h)
    return df


def build_station_features(g: pd.DataFrame, horizon: int = 24,
                           col: str = STATION_TARGET) -> pd.DataFrame:
    """Tek istasyonun saatlik tablosundan özellikler + `target_h{horizon}` (ham ölçüm).

    - Özelliklerde istasyon serisinin boşlukları yalnızca GEÇMİŞ değerle (ileri taşıma, en fazla
      3 saat) doldurulur; interpolasyon sonraki ölçümü kullanacağı için sızıntı olurdu.
    - Hedef hiç doldurulmaz: yalnızca gerçekten ölçülmüş saatler hedef olur.
    """
    raw = g[col]
    work = g.copy()
    work[col] = raw.ffill(limit=FEATURE_FFILL_HOURS)
    out = build_features(work, horizon, col=col)
    out = add_cams_forecast(out, horizon)
    out[f"target_h{horizon}"] = raw.shift(-horizon)
    return out


def build_all_stations(df: pd.DataFrame, horizon: int = 24) -> pd.DataFrame:
    parts = [build_station_features(g, horizon)
             for _, g in df.groupby("station", sort=False, observed=True)]
    return pd.concat(parts)


NON_FEATURES = {"city", "station"}


def feature_columns(df: pd.DataFrame, realistic: bool = False) -> list[str]:
    """Modele girecek sütunlar: birim adları ve hedefler hariç her şey.

    realistic=True: CAMS'ın gelecek değerlerini (`cams_` önekli, iyimser vekil) dışarıda bırakır.
    """
    cols = [c for c in df.columns if c not in NON_FEATURES and not c.startswith("target_")]
    if realistic:
        cols = [c for c in cols if not c.startswith("cams_")]
    return cols
