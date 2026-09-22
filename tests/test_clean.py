import numpy as np
import pandas as pd

from havauyari.data.clean import clean


def _raw(pm25, pm10=None, humidity=None):
    n = len(pm25)
    idx = pd.date_range("2024-01-01", periods=n, freq="h")
    return pd.DataFrame(
        {
            "city": "test",
            "pm2_5": pm25,
            "pm10": pm10 if pm10 is not None else [100.0] * n,
            "relative_humidity_2m": humidity if humidity is not None else [50.0] * n,
        },
        index=idx,
    )


def test_missing_hours_are_added_and_short_gaps_filled():
    df = _raw([10.0, 20.0, 30.0, 40.0]).drop(index=pd.Timestamp("2024-01-01 01:00"))
    out, log = clean(df)
    assert len(out) == 4
    assert log["eklenen_saat"] == 1
    assert out["pm2_5"].iloc[1] == 20.0  # doğrusal interpolasyon
    assert out["city"].eq("test").all()


def test_long_gaps_stay_nan():
    pm = [10.0] + [np.nan] * 5 + [20.0]
    out, log = clean(_raw(pm), max_gap_hours=3)
    assert out["pm2_5"].isna().sum() == 5  # 5 saatlik boşluğun hiçbir saati doldurulmaz
    assert log["kalan_bos"] == 5


def test_gap_at_limit_is_filled():
    pm = [10.0] + [np.nan] * 3 + [50.0]
    out, _ = clean(_raw(pm), max_gap_hours=3)
    assert out["pm2_5"].tolist() == [10.0, 20.0, 30.0, 40.0, 50.0]


def test_edge_gaps_not_extrapolated():
    out, _ = clean(_raw([np.nan, 10.0, 20.0, np.nan]))
    assert out["pm2_5"].isna().sum() == 2


def test_duplicates_removed():
    df = _raw([10.0, 20.0, 30.0])
    df = pd.concat([df, df.iloc[[1]].assign(pm2_5=99.0)])
    out, log = clean(df)
    assert log["tekrar_saat"] == 1
    assert out["pm2_5"].iloc[1] == 20.0  # ilk kayıt tutulur


def test_out_of_range_masked_then_interpolated():
    out, log = clean(_raw([10.0, 20.0, 30.0], humidity=[50.0, 150.0, 70.0]))
    assert log["sinir_disi"] == 1
    assert out["relative_humidity_2m"].iloc[1] == 60.0


def test_pm25_capped_at_pm10():
    out, log = clean(_raw([10.0, 50.0, 30.0], pm10=[20.0, 40.0, 35.0]))
    assert log["pm25_sinirlanan"] == 1
    assert out["pm2_5"].iloc[1] == 40.0
    assert (out["pm2_5"] <= out["pm10"]).all()


def test_spikes_are_preserved():
    pm = [10.0] * 10 + [150.0] + [10.0] * 10
    out, _ = clean(_raw(pm, pm10=[300.0] * 21))
    assert out["pm2_5"].max() == 150.0
