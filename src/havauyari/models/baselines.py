"""Basit referans modeller. Her ML modeli en az bunları geçmek zorunda.

Hepsi geri test "predictor" imzasını kullanır: `predict(train, test) -> np.ndarray`.
`train` ve `test`, features.build_features çıktısıdır; her test satırı t anını, tahmin ise t+h
anındaki değeri temsil eder.

`col` tahmin edilen seriyi (CAMS hedefinde "pm2_5", istasyon hedefinde "station_pm25"),
`group` ise serinin ait olduğu birimi ("city" / "station") belirtir.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from havauyari.config import TARGET

Predictor = Callable[[pd.DataFrame, pd.DataFrame], np.ndarray]


def persistence(col: str = TARGET) -> Predictor:
    """t+h tahmini = t anındaki son gözlem ("yarın da bugün gibi")."""
    return lambda train, test: test[col].to_numpy()


def seasonal_naive_weekly(col: str = TARGET) -> Predictor:
    """t+h tahmini = hedef anından tam 1 hafta önceki aynı saat (t+h-168)."""
    return lambda train, test: test[f"{col}_tgt_week_ago"].to_numpy()


def moving_average_24(col: str = TARGET) -> Predictor:
    """t+h tahmini = son 24 saatin ortalaması."""
    return lambda train, test: test[f"{col}_rollmean24"].to_numpy()


def climatology(horizon: int, col: str = TARGET, group: str = "city") -> Predictor:
    """t+h tahmini = eğitim verisinde aynı birim × ay × saatin medyanı ("tipik değer").

    Yalnızca eğitim penceresindeki gözlemlerden hesaplanır; test dönemi bilgisi kullanılmaz.
    """

    def predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
        obs = pd.DataFrame({"g": train[group].to_numpy(), "month": train.index.month,
                            "hour": train.index.hour, "value": train[col].to_numpy()})
        table = obs.groupby(["g", "month", "hour"], observed=True)["value"].median()
        tgt = test.index + pd.Timedelta(hours=horizon)
        keys = pd.MultiIndex.from_arrays([test[group].to_numpy(), tgt.month, tgt.hour],
                                         names=["g", "month", "hour"])
        return table.reindex(keys).to_numpy()

    return predict


def cams_raw(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """t+h tahmini = hedef anındaki CAMS değeri (istasyon koordinatında).

    Geçmiş CAMS tahmin arşivi olmadığı için CAMS'ın analiz değeri kullanılır; gerçek bir
    24 saatlik tahminden daha isabetli olduğundan CAMS lehine İYİMSER bir referanstır.
    """
    return test["cams_tgt"].to_numpy()


def cams_scaled(col: str = "station_pm25", group: str = "station") -> Predictor:
    """Ham CAMS × (eğitimde birim ortalaması / CAMS ortalaması): basit sapma düzeltmesi."""

    def predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
        both = train[[group, col, "pm2_5"]].dropna()
        means = both.groupby(group, observed=True)[[col, "pm2_5"]].mean()
        ratio = (means[col] / means["pm2_5"]).reindex(test[group].to_numpy()).to_numpy()
        return test["cams_tgt"].to_numpy() * ratio

    return predict


def baseline_predictors(horizon: int, col: str = TARGET, group: str = "city",
                        with_cams: bool = False) -> dict[str, Predictor]:
    predictors: dict[str, Predictor] = {
        "persistence": persistence(col),
        "moving_avg_24": moving_average_24(col),
        "climatology": climatology(horizon, col, group),
    }
    if horizon <= 168:
        predictors["seasonal_naive_7d"] = seasonal_naive_weekly(col)
    if with_cams:
        predictors["cams_raw"] = cams_raw
        predictors["cams_scaled"] = cams_scaled(col, group)
    return predictors
