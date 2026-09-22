"""Basit referans modeller. Her ML modeli en az bunları geçmek zorunda.

Hepsi geri test "predictor" imzasını kullanır: `predict(train, test) -> np.ndarray`.
`train` ve `test`, features.build_features çıktısıdır; her test satırı t anını, tahmin ise t+h
anındaki PM2.5'i temsil eder. Hiçbiri t sonrasındaki ölçümü kullanmaz.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from havauyari.config import TARGET

Predictor = Callable[[pd.DataFrame, pd.DataFrame], np.ndarray]


def persistence(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """t+h tahmini = t anındaki son gözlem ("yarın da bugün gibi")."""
    return test[TARGET].to_numpy()


def seasonal_naive_weekly(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """t+h tahmini = hedef anından tam 1 hafta önceki aynı saat (t+h-168)."""
    return test[f"{TARGET}_tgt_week_ago"].to_numpy()


def moving_average_24(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """t+h tahmini = son 24 saatin ortalaması."""
    return test[f"{TARGET}_rollmean24"].to_numpy()


def climatology(horizon: int) -> Predictor:
    """t+h tahmini = eğitim verisinde aynı şehir × ay × saatin medyanı ("tipik değer").

    Yalnızca eğitim penceresindeki gözlemlerden hesaplanır; test dönemi bilgisi kullanılmaz.
    """

    def predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
        obs = pd.DataFrame({"city": train["city"].to_numpy(), "month": train.index.month,
                            "hour": train.index.hour, "value": train[TARGET].to_numpy()})
        table = obs.groupby(["city", "month", "hour"], observed=True)["value"].median()
        tgt = test.index + pd.Timedelta(hours=horizon)
        keys = pd.MultiIndex.from_arrays([test["city"].to_numpy(), tgt.month, tgt.hour],
                                         names=["city", "month", "hour"])
        return table.reindex(keys).to_numpy()

    return predict


def baseline_predictors(horizon: int) -> dict[str, Predictor]:
    predictors: dict[str, Predictor] = {
        "persistence": persistence,
        "moving_avg_24": moving_average_24,
        "climatology": climatology(horizon),
    }
    if horizon <= 168:
        predictors["seasonal_naive_7d"] = seasonal_naive_weekly
    return predictors
