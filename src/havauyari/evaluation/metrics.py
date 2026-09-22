"""Regresyon ve uyarı (alarm) metrikleri."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score

from havauyari.alerts.aqi import ALERT_INDEX, threshold_concentration


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


def exceeds(conc, threshold_index: int = ALERT_INDEX) -> np.ndarray:
    """Konsantrasyon eşik kategorisine ulaşıyor mu? EPA kuralı: 0,1'e aşağı yuvarlanır."""
    c = np.floor(np.asarray(conc, float) * 10 + 1e-9) / 10
    return c >= threshold_concentration(threshold_index)


def alert_metrics(y_true, y_pred, threshold_index: int = ALERT_INDEX) -> dict[str, float]:
    """Gerçek ve tahmin konsantrasyonlarını 'uyarı var/yok' ikili sınıfına çevirip ölçer.

    Erken uyarıda kaçırılan alarm (false negative) en pahalı hatadır, bu yüzden recall ana
    metriktir.
    """
    t, p = _clean(y_true, y_pred)
    t_alert, p_alert = exceeds(t, threshold_index), exceeds(p, threshold_index)
    kw = {"zero_division": 0}
    return {
        "alert_recall": float(recall_score(t_alert, p_alert, **kw)),
        "alert_precision": float(precision_score(t_alert, p_alert, **kw)),
        "alert_f1": float(f1_score(t_alert, p_alert, **kw)),
        "alert_rate": float(t_alert.mean()) if len(t_alert) else 0.0,
    }
