# Geri Test: İstasyon Ölçümü, 24 Saat Sonrası PM2.5

_Oluşturulma: 2026-09-22 · Üreten: `python -m havauyari.models.train_station`_

## Kurulum

- **Hedef:** Çevre Bakanlığı SİM istasyonunda **gerçekten ölçülen** saatlik PM2.5 (8 kentsel istasyon, 5 şehir). Ölçülmemiş saatler hedef olarak kullanılmaz.
- **Test:** 2025-09-23 → 2026-09-18, 12 × 30 gün walk-forward, genişleyen eğitim + arındırma.
- **Karşılaştırma:** tüm modeller aynı 62,625 (zaman, istasyon) satırında ölçülür. Gerçek uyarı oranı (PM2.5 ≥ 35.5): %15.1.
- **lgbm_gercekci** (99 özellik): istasyon geçmişi, CAMS'ın t anına kadarki değerleri, ERA5 gözlemleri ve *o gün yayımlanmış* 1 günlük hava tahminleri. Bugün birebir uygulanabilir → **alt sınır**.
- **lgbm_iyimser** (108 özellik): + CAMS'ın hedef anı ve öncesindeki değerleri. Geçmiş CAMS tahmin arşivi olmadığından CAMS analizi kullanılır; `cams_raw` ve `cams_scaled` referanslarıyla aynı avantaja sahiptir → **üst sınır**.

## Genel sonuç

| model | MAE | RMSE | uyarı recall | uyarı precision | uyarı F1 | recall ≥55,5 |
|---|---|---|---|---|---|---|
| lgbm_iyimser | 6.503 | 10.449 | 0.683 | 0.730 | 0.705 | 0.457 |
| lgbm_gercekci | 6.778 | 10.784 | 0.656 | 0.730 | 0.691 | 0.431 |
| moving_avg_24 | 9.086 | 14.119 | 0.570 | 0.614 | 0.591 | 0.414 |
| persistence | 9.094 | 14.509 | 0.602 | 0.604 | 0.603 | 0.493 |
| climatology | 10.303 | 17.031 | 0.051 | 0.359 | 0.090 | 0.000 |
| cams_scaled | 11.150 | 17.315 | 0.409 | 0.466 | 0.436 | 0.237 |
| seasonal_naive_7d | 11.609 | 18.317 | 0.486 | 0.486 | 0.486 | 0.361 |
| cams_raw | 12.949 | 19.730 | 0.250 | 0.361 | 0.295 | 0.101 |

- Gerçekçi model, en iyi referansa (moving_avg_24) göre MAE'de **%25.4**, ham CAMS'a göre **%47.7** iyi.
- İyimser model, ham CAMS'a göre **%49.8**, ölçeklenmiş CAMS'a göre **%41.7** iyi.

### Ankara hariç (düşük güvenli 2 istasyon çıkarıldığında)

| model | MAE | RMSE | uyarı recall | uyarı precision | uyarı F1 | recall ≥55,5 |
|---|---|---|---|---|---|---|
| lgbm_iyimser | 7.197 | 11.449 | 0.698 | 0.731 | 0.714 | 0.464 |
| lgbm_gercekci | 7.509 | 11.820 | 0.673 | 0.733 | 0.702 | 0.443 |
| moving_avg_24 | 9.959 | 15.308 | 0.588 | 0.623 | 0.605 | 0.424 |
| persistence | 10.057 | 15.861 | 0.611 | 0.613 | 0.612 | 0.498 |
| climatology | 11.493 | 18.722 | 0.054 | 0.359 | 0.094 | 0.000 |
| cams_scaled | 12.445 | 18.964 | 0.421 | 0.480 | 0.449 | 0.240 |
| seasonal_naive_7d | 12.576 | 19.618 | 0.512 | 0.510 | 0.511 | 0.372 |
| cams_raw | 13.298 | 20.149 | 0.235 | 0.462 | 0.312 | 0.090 |

## İstasyona göre

Ankara istasyonları düşük güvenlidir (kış gecesi değerleri şüpheli düşük; bkz. reports/istasyon_veri_kalitesi.md).

### MAE

| model | ankara_etimesgut | ankara_kecioren_sanatoryum | bursa | bursa_kultur_park_mthm | istanbul_sultangazi_mthm | istanbul_umraniye_mthm | izmir_konak | kocaeli |
|---|---|---|---|---|---|---|---|---|
| lgbm_iyimser | 4.14 | 4.68 | 8.66 | 8.33 | 4.88 | 3.82 | 10.88 | 6.46 |
| lgbm_gercekci | 4.28 | 4.86 | 9.07 | 8.30 | 5.27 | 4.12 | 11.45 | 6.68 |
| moving_avg_24 | 6.17 | 6.74 | 13.21 | 11.76 | 7.07 | 5.24 | 13.33 | 8.89 |
| persistence | 5.66 | 6.72 | 12.44 | 11.51 | 7.51 | 5.59 | 13.97 | 9.08 |
| climatology | 6.94 | 6.50 | 13.97 | 11.36 | 6.45 | 5.00 | 23.41 | 8.35 |
| cams_scaled | 6.76 | 7.73 | 12.95 | 13.83 | 11.09 | 6.40 | 20.61 | 9.30 |
| seasonal_naive_7d | 8.99 | 8.41 | 16.60 | 15.17 | 8.58 | 6.44 | 17.11 | 11.23 |
| cams_raw | 11.41 | 12.38 | 11.91 | 11.48 | 9.95 | 8.54 | 28.06 | 9.49 |

### Uyarı recall

| model | ankara_etimesgut | ankara_kecioren_sanatoryum | bursa | bursa_kultur_park_mthm | istanbul_sultangazi_mthm | istanbul_umraniye_mthm | izmir_konak | kocaeli |
|---|---|---|---|---|---|---|---|---|
| lgbm_iyimser | 0.451 | 0.349 | 0.691 | 0.621 | 0.508 | 0.355 | 0.791 | 0.571 |
| lgbm_gercekci | 0.386 | 0.333 | 0.659 | 0.638 | 0.331 | 0.135 | 0.788 | 0.513 |
| moving_avg_24 | 0.327 | 0.167 | 0.496 | 0.443 | 0.088 | 0.006 | 0.810 | 0.336 |
| persistence | 0.534 | 0.312 | 0.573 | 0.504 | 0.224 | 0.181 | 0.769 | 0.407 |
| climatology | 0.000 | 0.000 | 0.112 | 0.118 | 0.000 | 0.000 | 0.022 | 0.053 |
| cams_scaled | 0.183 | 0.253 | 0.530 | 0.407 | 0.780 | 0.639 | 0.327 | 0.440 |
| seasonal_naive_7d | 0.050 | 0.059 | 0.382 | 0.327 | 0.167 | 0.045 | 0.733 | 0.279 |
| cams_raw | 0.431 | 0.613 | 0.382 | 0.194 | 0.609 | 0.813 | 0.117 | 0.266 |

## Mevsime göre

### MAE

| model | Kış | İlkbahar | Yaz | Sonbahar |
|---|---|---|---|---|
| lgbm_iyimser | 9.51 | 5.55 | 3.71 | 7.23 |
| lgbm_gercekci | 9.82 | 5.89 | 3.81 | 7.58 |
| moving_avg_24 | 13.58 | 7.92 | 4.59 | 10.23 |
| persistence | 13.31 | 7.92 | 4.99 | 10.13 |
| climatology | 15.36 | 8.75 | 4.81 | 12.31 |
| cams_scaled | 15.92 | 9.76 | 6.51 | 12.39 |
| seasonal_naive_7d | 17.90 | 10.74 | 5.67 | 11.98 |
| cams_raw | 18.80 | 11.47 | 7.49 | 13.98 |

### Uyarı recall

| model | Kış | İlkbahar | Yaz | Sonbahar |
|---|---|---|---|---|
| lgbm_iyimser | 0.732 | 0.595 | 0.335 | 0.738 |
| lgbm_gercekci | 0.696 | 0.564 | 0.325 | 0.724 |
| moving_avg_24 | 0.628 | 0.425 | 0.219 | 0.655 |
| persistence | 0.631 | 0.526 | 0.338 | 0.663 |
| climatology | 0.088 | 0.044 | 0.025 | 0.015 |
| cams_scaled | 0.491 | 0.509 | 0.131 | 0.287 |
| seasonal_naive_7d | 0.510 | 0.391 | 0.224 | 0.565 |
| cams_raw | 0.334 | 0.263 | 0.017 | 0.174 |

