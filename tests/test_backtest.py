import numpy as np
import pandas as pd
import pytest

from havauyari.evaluation.backtest import (
    in_test_window,
    in_train_window,
    make_folds,
    run_backtest,
    summarize,
)
from havauyari.features.build import build_all_cities
from havauyari.models.baselines import baseline_predictors, climatology, persistence

H = 24


def _frame(days=120, cities=("a", "b")):
    idx = pd.date_range("2025-01-01", periods=days * 24, freq="h")
    parts = []
    for i, c in enumerate(cities):
        pm = 20 + 10 * np.sin(2 * np.pi * idx.hour / 24) + i * 5 + np.arange(len(idx)) * 0.001
        parts.append(pd.DataFrame({"city": c, "pm2_5": pm}, index=idx))
    return build_all_cities(pd.concat(parts), H)


def test_folds_are_contiguous_and_cover_end():
    idx = pd.date_range("2025-01-01", periods=400 * 24, freq="h")
    folds = make_folds(idx, n_folds=12, test_days=30)
    assert len(folds) == 12
    assert folds[-1].test_end == idx.max() + pd.Timedelta(hours=1)
    for prev, nxt in zip(folds, folds[1:], strict=False):
        assert prev.test_end == nxt.test_start
    assert all(f.test_end - f.test_start == pd.Timedelta(days=30) for f in folds)


@pytest.mark.parametrize("horizon", [1, 24, 72])
def test_purge_keeps_training_targets_before_test(horizon):
    idx = pd.date_range("2025-01-01", periods=100 * 24, freq="h")
    fold = make_folds(idx, n_folds=2, test_days=10)[0]
    tr = idx[in_train_window(idx, fold, horizon)]
    te = idx[in_test_window(idx, fold)]
    assert tr.max() + pd.Timedelta(hours=horizon) < fold.test_start
    # Arındırma tam olarak h saat kadar satırı dışarıda bırakır, fazlasını değil
    assert tr.max() == fold.test_start - pd.Timedelta(hours=horizon + 1)
    assert te.min() == fold.test_start and te.max() < fold.test_end


def test_run_backtest_shapes_and_truth():
    feats = _frame()
    folds = make_folds(feats.index, n_folds=3, test_days=10)
    preds = run_backtest(feats, H, {"persistence": persistence}, folds)
    assert len(preds) == 3 * 10 * 24 * 2 - H * 2  # son H saatin hedefi yok
    assert set(preds["fold"]) == {0, 1, 2}
    row = preds.iloc[100]
    truth = feats.loc[feats["city"] == row["city"], "pm2_5"]
    assert np.isclose(row["y_true"], truth.loc[row["target_time"]])
    assert np.isclose(row["y_pred"], truth.loc[row["time"]])


def test_predictor_never_sees_test_targets():
    feats = _frame()
    folds = make_folds(feats.index, n_folds=2, test_days=10)
    seen = []

    def spy(train, test):
        seen.append((train.index.max(), test.index.min()))
        return np.zeros(len(test))

    run_backtest(feats, H, {"spy": spy}, folds)
    for train_max, test_min in seen:
        assert train_max + pd.Timedelta(hours=H) < test_min


def test_climatology_uses_target_hour_and_train_only():
    # 1 Ocak – 1 Mart, önce "a" şehri. Eğitim ≤ 9 Şubat, test 20 Şubat.
    feats = _frame(days=60)
    train, test = feats.iloc[: 40 * 24], feats.iloc[50 * 24 : 51 * 24]
    pred = climatology(6)(train, test)
    tgt = test.index + pd.Timedelta(hours=6)
    a = train[(train["city"] == "a") & (train.index.month == 2)]
    expected = a.groupby(a.index.hour)["pm2_5"].median().reindex(tgt.hour).to_numpy()
    assert np.allclose(pred, expected)


def test_summarize_pooled_metrics():
    preds = pd.DataFrame({
        "model": ["m"] * 4, "season": ["Kış", "Kış", "Yaz", "Yaz"],
        "y_true": [10.0, 40.0, 10.0, 60.0], "y_pred": [12.0, 30.0, 10.0, 70.0],
    })
    s = summarize(preds)
    assert s.loc["m", "mae"] == pytest.approx((2 + 10 + 0 + 10) / 4)
    assert s.loc["m", "alert_recall"] == 0.5          # 40 ve 60 uyarı; yalnızca 60 yakalandı
    assert s.loc["m", "severe_recall"] == 1.0         # ≥55,5: yalnızca 60, yakalandı
    by = summarize(preds, ["season"])
    assert by.loc[("m", "Yaz"), "mae"] == 5.0


def test_baseline_set():
    assert set(baseline_predictors(24)) == {"persistence", "moving_avg_24", "climatology",
                                            "seasonal_naive_7d"}
    assert "seasonal_naive_7d" not in baseline_predictors(200)
