import numpy as np
import pandas as pd
import pytest

from havauyari.alerts.threshold import (
    GRID,
    OFFICIAL,
    apply_thresholds,
    binary_metrics,
    threshold_for_recall,
    walk_forward_thresholds,
)


def test_threshold_for_recall_picks_highest_meeting_target():
    # 10 gerçek uyarı; tahminleri 20, 21, ..., 29
    y_true = np.full(10, 50.0)
    y_pred = np.arange(20.0, 30.0)
    # recall ≥ 0.8 → en az 8 uyarı yakalanmalı → eşik ≤ 22
    assert threshold_for_recall(y_true, y_pred, 0.8) == 22.0
    assert threshold_for_recall(y_true, y_pred, 1.0) == 20.0


def test_threshold_never_exceeds_official_and_has_floor():
    y_true = np.full(5, 80.0)
    assert threshold_for_recall(y_true, np.full(5, 100.0), 0.8) == OFFICIAL
    assert threshold_for_recall(y_true, np.full(5, 1.0), 0.8) == GRID.min()


def test_threshold_ignores_nan_and_handles_no_alerts():
    assert threshold_for_recall([np.nan, 50.0], [40.0, 36.0], 0.8) == OFFICIAL
    assert threshold_for_recall([10.0, 12.0], [5.0, 6.0], 0.8) == GRID.max()


def _preds(n_folds=4, per_fold=50, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for k in range(n_folds):
        t = pd.date_range("2025-01-01", periods=per_fold, freq="h") + pd.Timedelta(days=30 * k)
        y = rng.uniform(0, 80, per_fold)
        rows.append(pd.DataFrame({"time": t, "station": "s", "fold": k, "y_true": y,
                                  "y_pred": y * 0.7 + rng.normal(0, 3, per_fold)}))
    return pd.concat(rows, ignore_index=True)


def test_walk_forward_uses_only_past_folds():
    p = _preds()
    base = walk_forward_thresholds(p, [2, 3])
    changed = p.copy()
    changed.loc[changed["fold"] == 3, "y_pred"] = 0.0          # gelecek pencereyi boz
    assert walk_forward_thresholds(changed, [2])[2] == base[2]
    changed.loc[changed["fold"] == 1, "y_pred"] = 0.0          # geçmişi boz
    assert walk_forward_thresholds(changed, [2])[2] != base[2]


def test_walk_forward_requires_history():
    with pytest.raises(ValueError):
        walk_forward_thresholds(_preds(), [0])


def test_group_thresholds_use_own_history_and_fallback():
    from havauyari.alerts.threshold import walk_forward_group_thresholds

    rows = []
    for k in range(3):
        for st, scale in (("a", 1.0), ("b", 0.5)):   # "b" istasyonu sistematik düşük tahmin
            y = np.full(100, 50.0)
            rows.append(pd.DataFrame({"fold": k, "station": st, "y_true": y,
                                      "y_pred": y * scale + np.linspace(-5, 5, 100)}))
    p = pd.concat(rows, ignore_index=True)
    thr = walk_forward_group_thresholds(p, [2], "station", min_alerts=50)
    a = thr[(p["fold"] == 2) & (p["station"] == "a")].iloc[0]
    b = thr[(p["fold"] == 2) & (p["station"] == "b")].iloc[0]
    assert b < a                                     # düşük tahmin eden istasyona düşük eşik
    assert thr[p["fold"] < 2].isna().all()           # yalnızca değerlendirme pencereleri
    # Yeterli uyarı yoksa genel eşiğe düşer
    fb = walk_forward_group_thresholds(p, [2], "station", min_alerts=10_000)
    assert fb[p["fold"] == 2].nunique() == 1


def test_apply_and_binary_metrics():
    p = _preds()
    q = apply_thresholds(p, {2: 25.0, 3: 30.0})
    assert set(q["fold"]) == {2, 3}
    assert (q.loc[q["fold"] == 3, "eşik"] == 30.0).all()
    m = binary_metrics([True, True, False, False], [True, False, True, False])
    assert m["recall"] == 0.5 and m["precision"] == 0.5 and m["f1"] == 0.5
