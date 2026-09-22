"""Basit referans modeller. Her ML modeli en az bunları geçmek zorunda.

Hepsi t anında t+h için tahmin üretir ve yalnızca geçmiş değerleri kullanır.
"""

from __future__ import annotations

import pandas as pd


def persistence(series: pd.Series, horizon: int) -> pd.Series:
    """t+h tahmini = t anındaki son gözlem."""
    return series.rename(f"persistence_h{horizon}")


def seasonal_naive(series: pd.Series, horizon: int, season: int = 24) -> pd.Series:
    """t+h tahmini = bir sezon önceki aynı saat (t+h-season)."""
    k = season * ((horizon - 1) // season + 1)  # h > season ise birden fazla sezon geri git
    return series.shift(k - horizon).rename(f"seasonal_naive_h{horizon}")


def moving_average(series: pd.Series, horizon: int, window: int = 24) -> pd.Series:
    """t+h tahmini = son `window` saatin ortalaması."""
    return series.rolling(window, min_periods=window // 2).mean().rename(f"ma{window}_h{horizon}")
