# Tahmin Aralıkları: İstasyon Hedefi, 24 Saat

_Oluşturulma: 2026-09-23 · Üreten: `python -m havauyari.models.intervals` · Model: `lgbm_gercekci`_

## Yöntem

Walk-forward conformal: her test penceresi için, yalnızca önceki pencerelerin kalıntıları (gerçek − tahmin) tahmin seviyesi dilimlerine ayrılır ve %10 / %90 yüzdelikleri alınır. Hedef kapsama %80. Değerlendirme: son 12 pencere.

## Genel

|  | kapsama | ort. genişlik | gerçek > üst sınır | gerçek < alt sınır |
|---|---|---|---|---|
| tümü | 0.829 | 23.199 | 0.088 | 0.082 |

## Gerçek değere göre kapsama

Zirvelerde nokta tahmin çok düşük kalıyordu (≥ 55,5'te −23 sapma); aralığın bu riski ne kadar gösterdiğine bakılır.

| gerçek_aralık | kapsama | ort. genişlik | saat |
|---|---|---|---|
| 0–10 | 0.778 | 12.553 | 18221 |
| 10–20 | 0.899 | 18.131 | 21273 |
| 20–35,5 | 0.854 | 28.227 | 15571 |
| 35,5–55,5 | 0.815 | 41.730 | 6096 |
| ≥55,5 | 0.594 | 53.270 | 3675 |

## Tahmin dilimine göre kapsama

| dilim | kapsama | ort. genişlik | saat |
|---|---|---|---|
| <10 | 0.818 | 9.990 | 15270 |
| 10–20 | 0.815 | 16.123 | 25067 |
| 20–30 | 0.860 | 28.047 | 11597 |
| 30–45 | 0.862 | 40.934 | 8003 |
| ≥45 | 0.809 | 60.124 | 4899 |

## Mevsime ve istasyona göre kapsama

| season | kapsama | ort. genişlik | saat |
|---|---|---|---|
| Kış | 0.742 | 26.810 | 16470 |
| Sonbahar | 0.824 | 26.206 | 15393 |
| Yaz | 0.898 | 17.581 | 16291 |
| İlkbahar | 0.854 | 22.345 | 16682 |

| station | kapsama | ort. genişlik | saat |
|---|---|---|---|
| ankara_etimesgut | 0.807 | 13.600 | 8080 |
| ankara_kecioren_sanatoryum | 0.768 | 13.876 | 8112 |
| bursa | 0.752 | 26.119 | 8238 |
| bursa_kultur_park_mthm | 0.776 | 24.794 | 8185 |
| istanbul_sultangazi_mthm | 0.901 | 21.388 | 8370 |
| istanbul_umraniye_mthm | 0.876 | 16.174 | 7886 |
| izmir_konak | 0.874 | 43.309 | 8213 |
| kocaeli | 0.883 | 25.967 | 7752 |

## Üst sınırın risk göstergesi olarak kullanımı (tanımlayıcı)

"Aralığın üst sınırı ≥ 35,5" koşulu gerçek uyarıların %95.2'ini kapsıyor (precision %38.7). Kullanıcıya uyarı kararı yerine "uyarı riski var" bilgisi olarak gösterilebilir.

Örnek: tahmin 29.3 µg/m³ → %80 aralık 16.5–45.3 (gerçekleşen 36.0).

## Canlı sistem tablosu

Tüm tahminlerden hesaplandı: `models/prediction_interval.json`

| tahmin dilimi | q_low | q_high | n |
|---|---|---|---|
| <10 | -4.34 | 5.71 | 28668 |
| 10–20 | -7.30 | 8.17 | 48191 |
| 20–30 | -12.03 | 14.10 | 22638 |
| 30–45 | -17.23 | 21.11 | 16339 |
| ≥45 | -28.73 | 31.11 | 9309 |

