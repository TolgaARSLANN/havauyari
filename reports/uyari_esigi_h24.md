# Uyarı Karar Eşiği: İstasyon Hedefi, 24 Saat

_Oluşturulma: 2026-09-23 · Üreten: `python -m havauyari.alerts.threshold` · Model: `lgbm_gercekci`_

## Yöntem

- Gerçek uyarı = ölçülen PM2.5 ≥ 35.5 µg/m³ (resmî eşik, değişmez).
- Karar kuralı: model tahmini ≥ karar eşiği ise uyar. Hedef: recall ≥ %80.
- Eşik seçimi: recall hedefini sağlayan **en yüksek** eşik (yanlış alarmı en aza indirir), aralık 15.0–35.5.
- **Walk-forward:** 24 aylık geri testin son 12 penceresi değerlendirilir; her pencerenin eşiği yalnızca kendisinden önceki pencerelerin tahminlerinden seçilir. İlk pencereler daha az veriyle eğitilmiş modellerden geldiği için seçilen eşikler hafif temkinlidir.

## Sonuç (son 12 ay)

| karar kuralı | recall | precision | f1 | gerçek_uyarı | uyarı saati / istasyon-hafta |
|---|---|---|---|---|---|
| sabit 35.5 | 0.657 | 0.734 | 0.693 | 9771 | 21.396 |
| walk-forward eşik | 0.824 | 0.572 | 0.676 | 9771 | 34.404 |

## Pencere bazında

| test başlangıcı | eşik | recall | precision | f1 | uyarı_saati | gerçek_uyarı |
|---|---|---|---|---|---|---|
| 2025-09-23 | 28.000 | 0.852 | 0.644 | 0.734 | 1220 | 922 |
| 2025-10-23 | 28.000 | 0.913 | 0.659 | 0.765 | 2496 | 1802 |
| 2025-11-22 | 28.500 | 0.924 | 0.631 | 0.750 | 2924 | 1996 |
| 2025-12-22 | 29.500 | 0.737 | 0.628 | 0.678 | 1282 | 1093 |
| 2026-01-21 | 29.500 | 0.697 | 0.706 | 0.701 | 1066 | 1081 |
| 2026-02-20 | 29.000 | 0.918 | 0.620 | 0.740 | 1641 | 1109 |
| 2026-03-22 | 29.500 | 0.727 | 0.514 | 0.602 | 886 | 626 |
| 2026-04-21 | 29.000 | 0.572 | 0.424 | 0.487 | 601 | 446 |
| 2026-05-21 | 29.000 | 0.331 | 0.179 | 0.232 | 296 | 160 |
| 2026-06-20 | 28.500 | 0.722 | 0.150 | 0.249 | 466 | 97 |
| 2026-07-20 | 28.500 | 0.851 | 0.304 | 0.448 | 602 | 215 |
| 2026-08-19 | 28.500 | 0.839 | 0.315 | 0.459 | 596 | 224 |

## İstasyon bazında

| istasyon | gerçek uyarı | recall (sabit 35.5) | recall (walk-forward) | precision (walk-forward) |
|---|---|---|---|---|
| ankara_etimesgut | 344 | 0.384 | 0.741 | 0.489 |
| ankara_kecioren_sanatoryum | 187 | 0.332 | 0.476 | 0.368 |
| bursa | 1671 | 0.659 | 0.800 | 0.644 |
| bursa_kultur_park_mthm | 1336 | 0.644 | 0.790 | 0.559 |
| istanbul_sultangazi_mthm | 516 | 0.329 | 0.554 | 0.338 |
| istanbul_umraniye_mthm | 169 | 0.124 | 0.391 | 0.269 |
| izmir_konak | 4478 | 0.790 | 0.934 | 0.649 |
| kocaeli | 1070 | 0.502 | 0.735 | 0.433 |

## Eşik stratejileri (istasyon / mevsim)

Aynı walk-forward kural, grup başına uygulanır; geçmişte grup için 50'den az uyarı varsa genel eşik kullanılır.

| strateji | recall | precision | F1 | yaz precision | en düşük istasyon recall | uyarı saati / ist.-hafta |
|---|---|---|---|---|---|---|
| tek eşik | 0.824 | 0.572 | 0.676 | 0.255 | 0.391 | 34.404 |
| mevsime göre | 0.825 | 0.555 | 0.663 | 0.259 | 0.385 | 35.525 |
| istasyona göre | 0.798 | 0.548 | 0.650 | 0.320 | 0.714 | 34.753 |

## Canlı sistem eşiği

Tüm 24 pencerenin tahminlerinden seçilen eşik: **28.5 µg/m³** (`models/alert_threshold.json`).

