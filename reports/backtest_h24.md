# Geri Test Sonuçları: 24 saat sonrası PM2.5

_Oluşturulma: 2026-09-22 · Üreten: `python -m havauyari.models.train --horizon 24`_

## Kurulum

- **Test dönemi:** 2025-09-23 → 2026-09-18, 12 ardışık 30 günlük pencere
- **Eğitim:** her pencerede, hedef anı test başlangıcından önce olan tüm satırlar (genişleyen pencere + arındırma)
- **Tahmin sayısı:** model başına 43,080 (5 şehir); gerçek uyarı oranı %10.4
- **Uyarı:** PM2.5 ≥ 35.5 µg/m³ (hassas gruplar için sağlıksız); ikinci kademe ≥ 55.5 µg/m³
- Metrikler tüm test tahminleri birleştirilerek hesaplanır (fold ortalaması değil).

## Genel sonuç

| model | MAE | RMSE | sMAPE % | uyarı recall | uyarı precision | uyarı F1 | recall ≥55.5 |
|---|---|---|---|---|---|---|---|
| lightgbm | 6.747 | 10.800 | 34.991 | 0.420 | 0.617 | 0.500 | 0.280 |
| persistence | 7.434 | 12.318 | 37.298 | 0.518 | 0.517 | 0.517 | 0.431 |
| climatology | 7.976 | 12.917 | 41.947 | 0.141 | 0.666 | 0.232 | 0.051 |
| moving_avg_24 | 9.028 | 14.121 | 44.803 | 0.286 | 0.368 | 0.322 | 0.150 |
| seasonal_naive_7d | 9.984 | 15.780 | 50.066 | 0.396 | 0.396 | 0.396 | 0.293 |

LightGBM, en iyi referans modele (persistence) göre MAE'de **%9.2** iyi.

## Mevsime göre

### MAE

| model | Kış | İlkbahar | Yaz | Sonbahar |
|---|---|---|---|---|
| lightgbm | 10.65 | 6.71 | 3.37 | 6.31 |
| persistence | 12.04 | 7.48 | 3.52 | 6.75 |
| climatology | 12.36 | 7.54 | 4.04 | 8.07 |
| moving_avg_24 | 15.10 | 8.87 | 4.12 | 8.08 |
| seasonal_naive_7d | 14.73 | 11.07 | 4.97 | 9.20 |

### Uyarı recall

| model | Kış | İlkbahar | Yaz | Sonbahar |
|---|---|---|---|---|
| lightgbm | 0.554 | 0.315 | 0.000 | 0.222 |
| persistence | 0.576 | 0.435 | 0.033 | 0.483 |
| climatology | 0.226 | 0.077 | 0.000 | 0.007 |
| moving_avg_24 | 0.354 | 0.190 | 0.000 | 0.234 |
| seasonal_naive_7d | 0.493 | 0.266 | 0.000 | 0.318 |

## Şehre göre

### MAE

| model | ankara | bursa | istanbul | izmir | kocaeli |
|---|---|---|---|---|---|
| lightgbm | 6.97 | 5.49 | 9.81 | 5.97 | 5.49 |
| persistence | 7.88 | 5.93 | 10.64 | 6.39 | 6.33 |
| climatology | 8.20 | 6.87 | 11.33 | 7.05 | 6.43 |
| moving_avg_24 | 10.24 | 7.18 | 12.57 | 7.87 | 7.29 |
| seasonal_naive_7d | 9.78 | 8.66 | 14.08 | 8.96 | 8.44 |

### Uyarı recall

| model | ankara | bursa | istanbul | izmir | kocaeli |
|---|---|---|---|---|---|
| lightgbm | 0.593 | 0.286 | 0.455 | 0.316 | 0.241 |
| persistence | 0.612 | 0.476 | 0.525 | 0.492 | 0.386 |
| climatology | 0.345 | 0.000 | 0.140 | 0.033 | 0.000 |
| moving_avg_24 | 0.282 | 0.201 | 0.400 | 0.169 | 0.224 |
| seasonal_naive_7d | 0.550 | 0.321 | 0.397 | 0.313 | 0.259 |

## Pencere bazında MAE

| test başlangıcı | lightgbm | persistence | climatology | moving_avg_24 | seasonal_naive_7d |
|---|---|---|---|---|---|
| 2025-09-23 | 5.29 | 6.16 | 5.94 | 7.07 | 7.70 |
| 2025-10-23 | 8.76 | 8.96 | 11.87 | 11.11 | 13.71 |
| 2025-11-22 | 10.95 | 12.65 | 16.03 | 16.11 | 13.94 |
| 2025-12-22 | 9.93 | 10.35 | 10.34 | 13.27 | 14.95 |
| 2026-01-21 | 10.69 | 12.48 | 11.05 | 15.14 | 14.62 |
| 2026-02-20 | 9.47 | 10.15 | 10.32 | 12.54 | 14.54 |
| 2026-03-22 | 6.15 | 7.36 | 6.87 | 8.83 | 9.73 |
| 2026-04-21 | 5.74 | 6.49 | 6.49 | 7.33 | 10.94 |
| 2026-05-21 | 4.30 | 4.89 | 4.78 | 5.62 | 6.71 |
| 2026-06-20 | 3.03 | 2.51 | 4.43 | 3.04 | 3.86 |
| 2026-07-20 | 2.99 | 3.37 | 3.50 | 3.91 | 4.63 |
| 2026-08-19 | 3.55 | 3.70 | 3.96 | 4.21 | 4.29 |

