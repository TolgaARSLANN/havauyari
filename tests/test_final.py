import lightgbm as lgb
import numpy as np
import pandas as pd

from havauyari.models.final import contributions, explain_row, family_of


def _model(seed=0):
    rng = np.random.default_rng(seed)
    X = pd.DataFrame({"fc_win_calm_hours": rng.uniform(0, 24, 800),
                      "station_pm25_lag1": rng.uniform(0, 80, 800),
                      "hour_sin": rng.uniform(-1, 1, 800)})
    y = 2 * X["fc_win_calm_hours"] + 0.5 * X["station_pm25_lag1"] + rng.normal(0, 1, 800)
    model = lgb.LGBMRegressor(n_estimators=50, verbose=-1).fit(X, y)
    return model.booster_, X


def test_contributions_sum_to_prediction():
    booster, X = _model()
    c = contributions(booster, X.head(20))
    assert np.allclose(c.sum(axis=1), booster.predict(X.head(20)), atol=1e-6)


def test_explain_row_accounts_for_whole_prediction():
    booster, X = _model()
    row = X.iloc[[3]]
    e = explain_row(booster, row, top=2)
    assert np.isclose(e["katkı (µg/m³)"].sum(), booster.predict(row)[0], atol=1e-6)
    assert {"diğer özellikler", "taban (ortalama)"} <= set(e.index)
    assert e.index[0] in {"fc_win_calm_hours", "station_pm25_lag1"}


def test_family_mapping():
    assert family_of("fc_win_calm_hours").startswith("hava tahmini")
    assert family_of("station_pm25_lag24").startswith("istasyon PM2.5")
    assert family_of("nitrogen_dioxide_lag24") == "CAMS diğer kirleticiler"
    assert family_of("pm_ratio_rollmean24") == "CAMS PM2.5 ve oranı"
    assert family_of("tgt_hour_sin") == "takvim ve hedef zamanı"
    assert family_of("wind_speed_rollmean24").startswith("meteoroloji")
