import numpy as np

from havauyari.evaluation.metrics import alert_metrics, regression_metrics


def test_regression_metrics_ignores_nan():
    m = regression_metrics([1, 2, np.nan], [2, 2, 5])
    assert m["n"] == 2
    assert m["mae"] == 0.5


def test_alert_recall():
    # 2 gerçek alarm (60, 80), model birini yakalıyor
    m = alert_metrics([10, 60, 80], [10, 70, 20])
    assert m["alert_recall"] == 0.5
    assert m["alert_precision"] == 1.0
