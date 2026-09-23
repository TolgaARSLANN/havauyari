# Deney: Zirve Bastırma, 24 Saat (İstasyon Hedefi)

_Oluşturulma: 2026-09-23 · Üreten: `python -m havauyari.models.experiments`_

## Adaylar

| aday | açıklama |
|---|---|
| l2 | Mevcut model: L2 kaybı, ham hedef (Faz 3.9) |
| log1p | L2 kaybı, log(1+PM2.5) hedef |
| tweedie | Tweedie kaybı (varyans gücü 1,5) |
| agirlikli | L2 kaybı, ağırlık = 1 + PM2.5 / 35,5 |
| siniflandirici | Doğrudan P(PM2.5 ≥ 35,5) tahmin eden ikili sınıflandırıcı |

## Protokol

24 aylık walk-forward geri test; son 12 pencere değerlendirilir. Her pencerenin uyarı karar eşiği yalnızca önceki pencerelerin tahminlerinden, recall ≥ %80 sağlayan en yüksek değer olarak seçilir. Ana ölçüt: bu recall düzeyinde **precision**.

## Sonuçlar

| aday | recall | precision | F1 | yeni başlayan recall | eşik aralığı | MAE | RMSE | sapma ≥55,5 | sapma <10 |
|---|---|---|---|---|---|---|---|---|---|
| l2 | 0.824 | 0.572 | 0.676 | 0.612 | 28–29.5 | 6.819 | 10.936 | -22.961 | 3.597 |
| log1p | 0.855 | 0.526 | 0.652 | 0.670 | 23–25 | 6.767 | 11.382 | -28.776 | 2.171 |
| tweedie | 0.860 | 0.526 | 0.653 | 0.680 | 24.5–26.5 | 6.731 | 11.127 | -26.629 | 2.858 |
| agirlikli | 0.834 | 0.565 | 0.674 | 0.635 | 28.5–30.5 | 7.043 | 11.091 | -22.020 | 4.172 |
| siniflandirici | 0.842 | 0.566 | 0.676 | 0.636 | 0.12–0.17 |  |  |  |  |

En yüksek precision: **l2** (0.572; mevcut model 0.572).

