"""Ham veriyi modellemeye hazır hale getirir.

Kullanım:
    python -m havauyari.data.clean      # data/raw/*.parquet -> data/processed/all_cities.parquet

Kurallar (gerekçeleri reports/veri_kalite_raporu.md ve docs/YOL_HARITASI.md Faz 1.2'de):
1. Saatlik frekans garanti edilir, tekrar eden saatlerden ilki tutulur.
2. Fiziksel sınır dışındaki değerler (config.PHYSICAL_LIMITS) NaN yapılır.
3. PM2.5, PM10'dan büyük olamaz (PM2.5 PM10'un alt kümesidir) -> PM10 ile sınırlanır.
4. En fazla `max_gap_hours` saatlik boşluklar zaman bazlı interpolasyonla doldurulur;
   daha uzun boşluklar NaN kalır ki model sahte veriden öğrenmesin.
5. Ani sıçramalar SİLİNMEZ: gerçek kirlilik olaylarıdır ve uyarı sisteminin hedefidir.
"""

from __future__ import annotations

import pandas as pd

from havauyari.config import PHYSICAL_LIMITS, PROCESSED_DIR, RAW_DIR

PROCESSED_PATH = PROCESSED_DIR / "all_cities.parquet"


def fill_short_gaps(s: pd.Series, max_gap_hours: int) -> pd.Series:
    """Yalnızca uzunluğu <= max_gap_hours olan iç boşlukları zaman bazlı interpolasyonla doldurur.

    pandas'ın `interpolate(limit=n)` parametresi uzun boşlukların da ilk n değerini doldurur;
    burada uzun boşluklar tamamen NaN bırakılır.
    """
    isna = s.isna()
    if not isna.any():
        return s
    run_id = (isna != isna.shift()).cumsum()
    run_len = isna.groupby(run_id).transform("size")
    short = isna & (run_len <= max_gap_hours)
    filled = s.interpolate(method="time", limit_area="inside")
    return s.where(~short, filled)


def clean(df: pd.DataFrame, max_gap_hours: int = 3) -> tuple[pd.DataFrame, dict[str, int]]:
    """Tek şehirlik ham tabloyu temizler. Dönüş: (temiz tablo, yapılan düzeltme sayıları)."""
    city = df["city"].iloc[0]
    df = df.drop(columns="city").sort_index()
    log: dict[str, int] = {"tekrar_saat": int(df.index.duplicated().sum())}

    df = df[~df.index.duplicated(keep="first")]
    n_before = len(df)
    df = df.asfreq("h")
    log["eklenen_saat"] = len(df) - n_before

    out_of_range = 0
    for col, (lo, hi) in PHYSICAL_LIMITS.items():
        if col in df:
            bad = (df[col] < lo) | (df[col] > hi)
            out_of_range += int(bad.sum())
            df[col] = df[col].mask(bad)
    log["sinir_disi"] = out_of_range

    if {"pm2_5", "pm10"} <= set(df.columns):
        over = df["pm2_5"] > df["pm10"]
        log["pm25_sinirlanan"] = int(over.sum())
        df.loc[over, "pm2_5"] = df.loc[over, "pm10"]

    num = df.select_dtypes("number").columns
    nan_before = int(df[num].isna().sum().sum())
    for col in num:
        df[col] = fill_short_gaps(df[col], max_gap_hours)
    nan_after = int(df[num].isna().sum().sum())
    log["doldurulan"] = nan_before - nan_after
    log["kalan_bos"] = nan_after

    df.insert(0, "city", city)
    return df, log


def build_processed() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tüm şehirleri temizleyip tek dosyaya yazar. Dönüş: (veri, şehir bazlı düzeltme özeti)."""
    paths = sorted(RAW_DIR.glob("*.parquet"))
    if not paths:
        raise FileNotFoundError(f"{RAW_DIR} boş. Önce fetch_openmeteo çalıştırın.")
    frames, logs = [], {}
    for p in paths:
        cleaned, log = clean(pd.read_parquet(p))
        frames.append(cleaned)
        logs[p.stem] = log
    df = pd.concat(frames)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED_PATH)
    return df, pd.DataFrame(logs).T


def main() -> None:
    df, summary = build_processed()
    print(summary.to_string())
    print(f"[ok] {len(df):,} satır, {df['city'].nunique()} şehir -> {PROCESSED_PATH}")


if __name__ == "__main__":
    main()
