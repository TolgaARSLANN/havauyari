import numpy as np
import pandas as pd
import pytest

from havauyari.models.intervals import (
    apply_intervals,
    residual_quantiles,
    walk_forward_intervals,
)


def _preds(n_folds=4, n=2000, seed=0):
    """Hata payı tahmin seviyesiyle büyüyen sentetik tahminler."""
    rng = np.random.default_rng(seed)
    rows = []
    for k in range(n_folds):
        pred = rng.uniform(1, 80, n)
        y = pred + rng.normal(0, 0.2 * pred + 1, n)
        rows.append(pd.DataFrame({"fold": k, "station": "s", "y_pred": pred, "y_true": y}))
    return pd.concat(rows, ignore_index=True)


def test_intervals_widen_with_prediction_level():
    p = _preds()
    t = residual_quantiles(p["y_true"], p["y_pred"])
    width = t["q_high"] - t["q_low"]
    assert width.is_monotonic_increasing
    lo, hi = apply_intervals([5.0, 60.0], t)
    assert hi[1] - lo[1] > hi[0] - lo[0]


def test_lower_bound_not_negative():
    t = residual_quantiles([0.0, 1.0, 2.0] * 50, [10.0, 12.0, 14.0] * 50)
    lo, _ = apply_intervals([1.0], t)
    assert lo[0] >= 0


def test_walk_forward_coverage_close_to_target():
    q = walk_forward_intervals(_preds(), [2, 3])
    assert set(q["fold"]) == {2, 3}
    assert abs(q["kapsandı"].mean() - 0.8) < 0.03


def test_walk_forward_ignores_future_folds():
    p = _preds()
    a = walk_forward_intervals(p, [2])
    changed = p.copy()
    changed.loc[changed["fold"] == 3, "y_true"] += 1000     # gelecek pencereyi boz
    b = walk_forward_intervals(changed, [2])
    pd.testing.assert_series_equal(a["hi"], b["hi"])
    with pytest.raises(ValueError):
        walk_forward_intervals(p, [0])
