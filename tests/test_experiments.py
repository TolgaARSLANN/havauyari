import numpy as np
import pandas as pd

from havauyari.alerts.threshold import PROBABILITY_GRID, threshold_for_recall
from havauyari.models.experiments import CANDIDATES, Candidate, make_predictor


def _frame(n=600, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2025-01-01", periods=n, freq="h")
    x = rng.uniform(0, 1, n)
    y = np.exp(1 + 3 * x + rng.normal(0, 0.2, n))          # sağa çarpık, pozitif hedef
    return pd.DataFrame({"station": "s", "city": "c", "x": x, "target_h24": y}, index=idx)


def test_candidate_names_unique_and_baseline_present():
    names = [c.name for c in CANDIDATES]
    assert len(names) == len(set(names)) and "l2" in names


def test_log1p_predictor_returns_original_scale():
    df = _frame()
    tr, te = df.iloc[:500], df.iloc[500:]
    raw = make_predictor(Candidate("l2", ""))(tr, te)
    logp = make_predictor(Candidate("log1p", "", transform="log1p"))(tr, te)
    # İki model aynı ölçekte tahmin üretmeli (log1p ters dönüşümü uygulanmış)
    assert np.all(logp > 0)
    assert abs(np.median(logp) - np.median(raw)) / np.median(raw) < 0.3


def test_classifier_outputs_probabilities():
    df = _frame()
    tr, te = df.iloc[:500], df.iloc[500:]
    p = make_predictor(Candidate("clf", "", kind="classifier"))(tr, te)
    assert np.all((p >= 0) & (p <= 1))
    # Yüksek x -> yüksek PM2.5 -> yüksek olasılık
    assert p[te["x"].to_numpy() > 0.8].mean() > p[te["x"].to_numpy() < 0.3].mean()


def test_threshold_on_probability_grid():
    y_true = np.array([50.0] * 10 + [5.0] * 10)
    prob = np.r_[np.linspace(0.5, 0.95, 10), np.linspace(0.0, 0.4, 10)]
    thr = threshold_for_recall(y_true, prob, 0.8, PROBABILITY_GRID)
    assert 0.5 <= thr <= 0.65
