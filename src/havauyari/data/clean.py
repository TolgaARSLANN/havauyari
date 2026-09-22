"""Ham veriyi modellemeye hazır hale getirir."""

from __future__ import annotations

import pandas as pd

from havauyari.config import PROCESSED_DIR, RAW_DIR


def clean(df: pd.DataFrame, max_gap_hours: int = 3) -> pd.DataFrame:
    """Saatlik frekansı garanti eder, kısa boşlukları doldurur, negatif değerleri atar.

    Sadece `max_gap_hours` kadar olan boşluklar zaman bazlı interpolasyonla doldurulur;
    daha uzun boşluklar NaN bırakılır ki model sahte veriden öğrenmesin.
    """
    city = df["city"].iloc[0]
    df = df.drop(columns="city").sort_index()
    df = df[~df.index.duplicated(keep="first")].asfreq("h")
    num = df.select_dtypes("number").columns
    df[num] = df[num].mask(df[num] < 0)
    df[num] = df[num].interpolate(method="time", limit=max_gap_hours, limit_area="inside")
    df.insert(0, "city", city)
    return df


def build_processed() -> pd.DataFrame:
    frames = [clean(pd.read_parquet(p)) for p in sorted(RAW_DIR.glob("*.parquet"))]
    if not frames:
        raise FileNotFoundError(f"{RAW_DIR} boş. Önce fetch_openmeteo çalıştırın.")
    df = pd.concat(frames)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED_DIR / "all_cities.parquet")
    return df


if __name__ == "__main__":
    out = build_processed()
    print(f"[ok] {len(out):,} satır, {out['city'].nunique()} şehir")
