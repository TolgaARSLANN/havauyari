"""Zaman serisi özellikleri.

Temel kural: t anındaki satırın özellikleri yalnızca t ve öncesindeki bilgiyi kullanır.
Hedef `target_h{h}` ise t+h anındaki değerdir (direkt çok-ufuklu strateji).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from havauyari.config import TARGET

LAGS = [1, 2, 3, 6, 12, 24, 48, 168]
ROLL_WINDOWS = [6, 24, 168]


def add_calendar(df: pd.DataFrame) -> pd.DataFrame:
    idx = df.index
    df["hour"] = idx.hour
    df["dayofweek"] = idx.dayofweek
    df["month"] = idx.month
    df["is_weekend"] = (idx.dayofweek >= 5).astype(int)
    # Döngüsel kodlama: 23 ile 0 saatinin birbirine yakın olduğunu modele söyler
    df["hour_sin"] = np.sin(2 * np.pi * idx.hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * idx.hour / 24)
    df["month_sin"] = np.sin(2 * np.pi * idx.month / 12)
    df["month_cos"] = np.cos(2 * np.pi * idx.month / 12)
    return df


def add_wind_vector(df: pd.DataFrame) -> pd.DataFrame:
    if {"wind_speed_10m", "wind_direction_10m"} <= set(df.columns):
        rad = np.deg2rad(df["wind_direction_10m"])
        df["wind_u"] = df["wind_speed_10m"] * np.sin(rad)
        df["wind_v"] = df["wind_speed_10m"] * np.cos(rad)
    return df


def add_lags(df: pd.DataFrame, col: str = TARGET) -> pd.DataFrame:
    for lag in LAGS:
        df[f"{col}_lag{lag}"] = df[col].shift(lag)
    # shift(1): pencere t'yi değil t-1'e kadarını kapsar, böylece "şimdiki" gözlem de sızmaz
    past = df[col].shift(1)
    for w in ROLL_WINDOWS:
        df[f"{col}_rollmean{w}"] = past.rolling(w, min_periods=w // 2).mean()
        df[f"{col}_rollstd{w}"] = past.rolling(w, min_periods=w // 2).std()
    return df


def add_targets(df: pd.DataFrame, horizons: list[int], col: str = TARGET) -> pd.DataFrame:
    for h in horizons:
        df[f"target_h{h}"] = df[col].shift(-h)
    return df


def build_features(
    df: pd.DataFrame, horizons: list[int] = (24,), col: str = TARGET
) -> pd.DataFrame:
    """Tek şehirlik saatlik tabloya tüm özellikleri ve hedefleri ekler."""
    out = df.copy()
    out = add_calendar(out)
    out = add_wind_vector(out)
    out = add_lags(out, col)
    out = add_targets(out, list(horizons), col)
    return out


def build_all_cities(df: pd.DataFrame, horizons: list[int] = (24,)) -> pd.DataFrame:
    """Lag'ler şehirler arasında karışmasın diye her şehri ayrı işler."""
    parts = [build_features(g, horizons) for _, g in df.groupby("city", sort=False)]
    return pd.concat(parts)
