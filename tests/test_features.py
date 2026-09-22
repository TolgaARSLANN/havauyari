import numpy as np
import pandas as pd

from havauyari.features.build import build_all_cities, build_features
from havauyari.models.baselines import seasonal_naive


def _series(n=400, city="x"):
    idx = pd.date_range("2024-01-01", periods=n, freq="h")
    return pd.DataFrame({"city": city, "pm2_5": np.arange(n, dtype=float)}, index=idx)


def test_no_future_leakage_in_features():
    """Özellikler t anında yalnızca <= t bilgisi içermeli."""
    df = _series()
    out = build_features(df, horizons=[24])
    t = out.index[200]
    row = out.loc[t]
    assert row["pm2_5_lag1"] == 199
    assert row["pm2_5_rollmean6"] == np.mean(range(194, 200))
    assert row["target_h24"] == 224
    feature_cols = [c for c in out.columns if c.startswith("pm2_5_")]
    assert (out.loc[t, feature_cols] < 200).all()


def test_lags_do_not_cross_cities():
    df = pd.concat([_series(200, "a"), _series(200, "b")])
    out = build_all_cities(df)
    first_b = out[out["city"] == "b"].iloc[0]
    assert np.isnan(first_b["pm2_5_lag1"])


def test_seasonal_naive_alignment():
    s = _series()["pm2_5"]
    # h=3, sezon=24: t+3 için t+3-24 = t-21 anındaki değer
    p = seasonal_naive(s, horizon=3, season=24)
    assert p.iloc[100] == 79
