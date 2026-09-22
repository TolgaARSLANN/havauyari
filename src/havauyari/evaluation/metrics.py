"""Regresyon ve uyarı (alarm) metrikleri."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score

from havauyari.alerts.aqi import UNHEALTHY_INDEX, category_index


def _clean(y_true, y_pred):
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    return y_true[mask], y_pred[mask]


def regression_metrics(y_true, y_pred) -> dict[str, float]:
    t, p = _clean(y_true, y_pred)
    err = p - t
    denom = (np.abs(t) + np.abs(p)) / 2
    smape = np.mean(np.where(denom == 0, 0, np.abs(err) / np.where(denom == 0, 1, denom))) * 100
    return {
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err**2))),
        "smape": float(smape),
        "n": int(len(t)),
    }


def alert_metrics(y_true, y_pred, threshold_index: int = UNHEALTHY_INDEX) -> dict[str, float]:
    """Gerçek ve tahmin konsantrasyonlarını 'uyarı var/yok' ikili sınıfına çevirip ölçer.

    Erken uyarıda kaçırılan alarm (false negative) en pahalı hatadır, bu yüzden recall ana
    metriktir.
    """
    t, p = _clean(y_true, y_pred)
    t_alert = np.array([category_index(v) >= threshold_index for v in t])
    p_alert = np.array([category_index(v) >= threshold_index for v in p])
    kw = {"zero_division": 0}
    return {
        "alert_recall": float(recall_score(t_alert, p_alert, **kw)),
        "alert_precision": float(precision_score(t_alert, p_alert, **kw)),
        "alert_f1": float(f1_score(t_alert, p_alert, **kw)),
        "alert_rate": float(t_alert.mean()) if len(t_alert) else 0.0,
    }
