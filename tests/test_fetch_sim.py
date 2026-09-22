"""SİM modülünün ağ gerektirmeyen parçalarının testleri."""

from datetime import datetime

import numpy as np
import pandas as pd

from havauyari.data.fetch_sim import _chunks, rows_to_frame, select_stations, slugify


def test_slugify_turkish_names():
    assert slugify("İstanbul - Ümraniye-MTHM") == "istanbul_umraniye_mthm"
    assert slugify("Ankara - Keçiören Sanatoryum") == "ankara_kecioren_sanatoryum"
    assert slugify("İzmir - Karşıyaka İBB") == "izmir_karsiyaka_ibb"
    assert slugify("Bursa - Uludağ Üniv.-MTHM") == "bursa_uludag_univ_mthm"


def test_rows_to_frame_parses_and_fills_missing_parameter():
    rows = [
        {"ReadTime": "2026-01-01T00:00:00", "Stationid": "x", "PM25": 12.5, "PM10": 20},
        {"ReadTime": "2026-01-01T01:00:00", "Stationid": "x", "PM25": None, "PM10": "-"},
    ]
    df = rows_to_frame(rows, ["PM25", "PM10", "NO2"])
    assert list(df.columns) == ["time", "station_id", "PM25", "PM10", "NO2"]
    assert df["time"].iloc[1] == pd.Timestamp("2026-01-01 01:00")
    assert df["PM25"].iloc[0] == 12.5 and np.isnan(df["PM25"].iloc[1])
    assert np.isnan(df["PM10"].iloc[1])      # sayı olmayan değer NaN olur
    assert df["NO2"].isna().all()            # yanıtta olmayan parametre
    assert rows_to_frame([], ["PM25"]).empty


def test_chunks_cover_range_without_gaps():
    parts = list(_chunks(datetime(2023, 1, 1), datetime(2025, 3, 15), months=12))
    assert parts[0][0] == datetime(2023, 1, 1)
    assert parts[-1][1] == datetime(2025, 3, 15)
    assert all(a[1] == b[0] for a, b in zip(parts, parts[1:], strict=False))
    assert len(parts) == 3


def test_select_stations_rules():
    df = pd.DataFrame([
        # şehir, ad, alan, kaynak, kapsam, son yıl
        ("a", "a-kentsel-iyi", "Kentsel", "Isınma", 95, 95),
        ("a", "a-sanayi", "Kentsel", "Sanayi", 99, 99),          # sanayi: elenir
        ("a", "a-kent-cevresi", "Kent Çevresi", "Trafik", 99, 99),  # kentsel değil: elenir
        ("a", "a-kentsel-orta", "Kentsel", "Trafik", 90, 85),
        ("a", "a-kentsel-ucuncu", "Kentsel", "Trafik", 85, 85),  # şehir başına 2 sınırı
        ("b", "b-son-yil-eksik", "Kentsel", "Isınma", 95, 60),   # son yıl < %80: elenir
    ], columns=["city", "name", "area_type", "source_type", "kapsam_%", "son_1_yil_%"])
    df["id"] = df["name"]
    picked = select_stations(df, per_city=2)
    assert picked["name"].tolist() == ["a-kentsel-iyi", "a-kentsel-orta"]
