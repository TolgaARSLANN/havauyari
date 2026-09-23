import numpy as np
import pandas as pd

from havauyari.evaluation.error_analysis import (
    COMPARE,
    MAIN,
    onset_vs_continuing,
    threshold_tradeoff,
)


def _wide(y_true, now, main_pred):
    n = len(y_true)
    idx = pd.MultiIndex.from_arrays(
        [pd.date_range("2025-12-01", periods=n, freq="h"), ["s1"] * n], names=["time", "station"])
    return pd.DataFrame({
        "y_true": y_true,
        "persistence": now,                       # t anındaki istasyon değeri
        MAIN: main_pred,
        "cams_raw": [10.0] * n,
        "target_time": pd.date_range("2025-12-02", periods=n, freq="h"),
    }, index=idx)


def test_onset_vs_continuing_split():
    #          yeni   yeni   süren  süren  uyarı yok
    y_true = [40.0, 50.0, 60.0, 45.0, 10.0]
    now = [10.0, 20.0, 50.0, 40.0, 10.0]
    main = [36.0, 20.0, 50.0, 30.0, 5.0]      # 1 yeni + 1 süren yakalandı
    out = onset_vs_continuing(_wide(y_true, now, main))
    assert out.loc["YENİ başlayan", "uyarı saati"] == 2
    assert out.loc["süren", "uyarı saati"] == 2
    assert out.loc["YENİ başlayan", f"recall {MAIN}"] == 0.5
    assert out.loc["YENİ başlayan", "recall persistence"] == 0.0
    assert out.loc["süren", "recall persistence"] == 1.0
    recall_models = {c.removeprefix("recall ") for c in out.columns if c.startswith("recall")}
    assert set(COMPARE) <= recall_models


def test_threshold_tradeoff_monotonic():
    rng = np.random.default_rng(0)
    y = rng.uniform(0, 80, 500)
    w = _wide(y, y, y + rng.normal(0, 8, 500))
    t = threshold_tradeoff(w)
    assert t["recall"].is_monotonic_decreasing
    assert t.loc[20.0, "recall"] > t.loc[40.0, "recall"]
    assert t.loc[40.0, "precision"] > t.loc[20.0, "precision"]
